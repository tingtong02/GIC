from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader, Dataset

from gic.eval import build_reconstruction_maps, summarize_prediction_rows
from gic.eval.case_studies import build_case_studies
from gic.eval.hotspot_metrics import summarize_hotspot_rows
from gic.eval.reporting import write_json_report
from gic.graph.datasets import GraphDataset, TemporalGraphSequenceExample, load_temporal_graph_examples
from gic.losses import LossComposer
from gic.models import MainModelInputBundle, MainModelOutputBundle, build_main_model
from gic.training.checkpoint import load_checkpoint, save_checkpoint


@dataclass(slots=True)
class FeatureGroupTransform:
    group_name: str
    feature_names: list[str]
    active_indices: list[int]
    active_names: list[str]
    mean: list[float]
    std: list[float]
    dropped_zero_variance: list[str] = field(default_factory=list)

    @property
    def dim(self) -> int:
        return len(self.active_indices)

    def summary(self) -> dict[str, Any]:
        return {
            'feature_count': len(self.feature_names),
            'active_count': len(self.active_names),
            'active_names': list(self.active_names),
            'dropped_zero_variance': list(self.dropped_zero_variance),
            'dropped_zero_variance_count': len(self.dropped_zero_variance),
        }

    def to_metadata(self) -> dict[str, Any]:
        return {
            'group_name': self.group_name,
            'feature_names': list(self.feature_names),
            'active_indices': list(self.active_indices),
            'active_names': list(self.active_names),
            'mean': list(self.mean),
            'std': list(self.std),
            'dropped_zero_variance': list(self.dropped_zero_variance),
        }

    @classmethod
    def from_metadata(cls, payload: dict[str, Any]) -> 'FeatureGroupTransform':
        return cls(
            group_name=str(payload.get('group_name', '')),
            feature_names=[str(item) for item in payload.get('feature_names', [])],
            active_indices=[int(item) for item in payload.get('active_indices', [])],
            active_names=[str(item) for item in payload.get('active_names', [])],
            mean=[float(item) for item in payload.get('mean', [])],
            std=[float(item) for item in payload.get('std', [])],
            dropped_zero_variance=[str(item) for item in payload.get('dropped_zero_variance', [])],
        )


@dataclass(slots=True)
class FeatureTransformBundle:
    node_features: FeatureGroupTransform
    global_signal_features: FeatureGroupTransform
    node_physics_features: FeatureGroupTransform
    global_physics_features: FeatureGroupTransform

    def combined_active_feature_names(self) -> list[str]:
        return [
            *self.node_features.active_names,
            *self.global_signal_features.active_names,
            *self.node_physics_features.active_names,
            *self.global_physics_features.active_names,
        ]

    def feature_summary(self) -> dict[str, Any]:
        return {
            'node_features': self.node_features.summary(),
            'global_signal_features': self.global_signal_features.summary(),
            'node_physics_features': self.node_physics_features.summary(),
            'global_physics_features': self.global_physics_features.summary(),
        }

    def model_input_dims(self) -> dict[str, int]:
        return {
            'node_input_dim': self.node_features.dim,
            'global_signal_dim': self.global_signal_features.dim,
            'node_physics_dim': self.node_physics_features.dim,
            'global_physics_dim': self.global_physics_features.dim,
        }

    def to_metadata(self) -> dict[str, Any]:
        return {
            'node_features': self.node_features.to_metadata(),
            'global_signal_features': self.global_signal_features.to_metadata(),
            'node_physics_features': self.node_physics_features.to_metadata(),
            'global_physics_features': self.global_physics_features.to_metadata(),
        }

    @classmethod
    def from_metadata(cls, payload: dict[str, Any]) -> 'FeatureTransformBundle':
        return cls(
            node_features=FeatureGroupTransform.from_metadata(dict(payload.get('node_features', {}))),
            global_signal_features=FeatureGroupTransform.from_metadata(dict(payload.get('global_signal_features', {}))),
            node_physics_features=FeatureGroupTransform.from_metadata(dict(payload.get('node_physics_features', {}))),
            global_physics_features=FeatureGroupTransform.from_metadata(dict(payload.get('global_physics_features', {}))),
        )


@dataclass(slots=True)
class MainModelTrainingResult:
    dataset_path: str
    checkpoint_path: str
    history_path: str
    best_epoch: int
    input_dim: int
    feature_names: list[str]
    feature_summary: dict[str, Any]
    signal_summary: dict[str, Any]
    dataset_summary: dict[str, Any]
    model_input_dims: dict[str, int]
    train_example_count: int
    val_example_count: int
    test_example_count: int
    validation_metrics: dict[str, Any]
    validation_hotspot_metrics: dict[str, Any]
    test_metrics: dict[str, Any]
    test_hotspot_metrics: dict[str, Any]


class TemporalSequenceDataset(Dataset[TemporalGraphSequenceExample]):
    def __init__(self, examples: list[TemporalGraphSequenceExample]) -> None:
        self.examples = examples

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> TemporalGraphSequenceExample:
        return self.examples[index]


def _set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)


def _stack_feature_rows(rows: Iterable[Iterable[float]], feature_count: int) -> torch.Tensor:
    collected = [list(row) for row in rows]
    if feature_count <= 0:
        return torch.zeros((len(collected), 0), dtype=torch.float32)
    if not collected:
        return torch.zeros((0, feature_count), dtype=torch.float32)
    return torch.tensor(collected, dtype=torch.float32)


def _flatten_sequence_node_rows(examples: list[TemporalGraphSequenceExample]) -> torch.Tensor:
    feature_count = len(examples[0].node_feature_names) if examples else 0
    rows = [row for item in examples for step in item.sequence_node_features for row in step]
    return _stack_feature_rows(rows, feature_count)


def _flatten_sequence_global_rows(examples: list[TemporalGraphSequenceExample]) -> torch.Tensor:
    feature_count = len(examples[0].global_signal_feature_names) if examples else 0
    rows = [row for item in examples for row in item.sequence_global_signal_features]
    return _stack_feature_rows(rows, feature_count)


def _flatten_node_physics_rows(examples: list[TemporalGraphSequenceExample]) -> torch.Tensor:
    feature_count = len(examples[0].node_physics_feature_names) if examples else 0
    rows = [row for item in examples for row in item.node_physics_features]
    return _stack_feature_rows(rows, feature_count)


def _flatten_global_physics_rows(examples: list[TemporalGraphSequenceExample]) -> torch.Tensor:
    feature_count = len(examples[0].global_physics_feature_names) if examples else 0
    rows = [item.global_physics_features for item in examples]
    return _stack_feature_rows(rows, feature_count)


def _build_feature_group_transform(
    *,
    group_name: str,
    feature_names: list[str],
    values: torch.Tensor,
    enabled: bool,
    drop_zero_variance: bool = True,
) -> FeatureGroupTransform:
    if not enabled or not feature_names:
        return FeatureGroupTransform(group_name, list(feature_names), [], [], [], [], [])
    feature_count = len(feature_names)
    if values.ndim != 2 or values.shape[1] != feature_count:
        values = torch.zeros((0, feature_count), dtype=torch.float32)
    variances = values.var(dim=0, unbiased=False) if values.shape[0] > 0 else torch.zeros(feature_count, dtype=torch.float32)
    active_indices: list[int] = []
    dropped_zero_variance: list[str] = []
    for index, name in enumerate(feature_names):
        variance = float(variances[index].item()) if variances.numel() > 0 else 0.0
        if drop_zero_variance and variance <= 1e-12:
            dropped_zero_variance.append(name)
            continue
        active_indices.append(index)
    if not active_indices:
        return FeatureGroupTransform(group_name, list(feature_names), [], [], [], [], dropped_zero_variance)
    selected = values[:, active_indices] if values.shape[0] > 0 else torch.zeros((0, len(active_indices)), dtype=torch.float32)
    if selected.shape[0] == 0:
        mean = [0.0 for _ in active_indices]
        std = [1.0 for _ in active_indices]
    else:
        mean_tensor = selected.mean(dim=0)
        std_tensor = selected.std(dim=0, unbiased=False).clamp(min=1e-6)
        mean = [float(item) for item in mean_tensor.tolist()]
        std = [float(item) for item in std_tensor.tolist()]
    return FeatureGroupTransform(
        group_name=group_name,
        feature_names=list(feature_names),
        active_indices=active_indices,
        active_names=[feature_names[index] for index in active_indices],
        mean=mean,
        std=std,
        dropped_zero_variance=dropped_zero_variance,
    )


def _prepare_feature_transforms(examples: list[TemporalGraphSequenceExample], config: dict[str, Any]) -> FeatureTransformBundle:
    if not examples:
        raise ValueError('Feature transforms require at least one training example')
    model_cfg = dict(config.get('model', {}))
    use_signal_features = bool(model_cfg.get('use_signal_features', True))
    use_physics_features = bool(model_cfg.get('use_physics_features', True))
    node_transform = _build_feature_group_transform(
        group_name='node_features',
        feature_names=list(examples[0].node_feature_names),
        values=_flatten_sequence_node_rows(examples),
        enabled=True,
        drop_zero_variance=False,
    )
    signal_transform = _build_feature_group_transform(
        group_name='global_signal_features',
        feature_names=list(examples[0].global_signal_feature_names),
        values=_flatten_sequence_global_rows(examples),
        enabled=use_signal_features,
        drop_zero_variance=True,
    )
    node_physics_transform = _build_feature_group_transform(
        group_name='node_physics_features',
        feature_names=list(examples[0].node_physics_feature_names),
        values=_flatten_node_physics_rows(examples),
        enabled=use_physics_features,
        drop_zero_variance=True,
    )
    global_physics_transform = _build_feature_group_transform(
        group_name='global_physics_features',
        feature_names=list(examples[0].global_physics_feature_names),
        values=_flatten_global_physics_rows(examples),
        enabled=use_physics_features,
        drop_zero_variance=True,
    )
    if node_transform.dim == 0:
        raise ValueError('Phase 5 feature selection removed every node input feature')
    return FeatureTransformBundle(
        node_features=node_transform,
        global_signal_features=signal_transform,
        node_physics_features=node_physics_transform,
        global_physics_features=global_physics_transform,
    )


def _select_and_normalize(values: torch.Tensor, transform: FeatureGroupTransform) -> torch.Tensor:
    batch_shape = values.shape[:-1]
    if transform.dim == 0:
        return values.new_zeros(*batch_shape, 0)
    index_tensor = torch.tensor(transform.active_indices, dtype=torch.long)
    selected = values.index_select(-1, index_tensor)
    shape = [1] * (selected.ndim - 1) + [transform.dim]
    mean = selected.new_tensor(transform.mean).view(*shape)
    std = selected.new_tensor(transform.std).view(*shape)
    return (selected - mean) / std.clamp(min=1e-6)


def _collate_temporal_examples(items: list[TemporalGraphSequenceExample], transforms: FeatureTransformBundle) -> MainModelInputBundle:
    batch_size = len(items)
    step_count = len(items[0].sequence_node_features)
    node_count = len(items[0].metadata)
    node_feature_count = len(items[0].node_feature_names)
    signal_feature_count = len(items[0].global_signal_feature_names)
    node_physics_count = len(items[0].node_physics_feature_names)
    global_physics_count = len(items[0].global_physics_feature_names)
    sequence_node_tensor = torch.tensor([item.sequence_node_features for item in items], dtype=torch.float32)
    sequence_signal_tensor = torch.tensor([item.sequence_global_signal_features for item in items], dtype=torch.float32)
    node_physics_tensor = torch.tensor([item.node_physics_features for item in items], dtype=torch.float32)
    global_physics_tensor = torch.tensor([item.global_physics_features for item in items], dtype=torch.float32)
    hotspot_targets = None
    if items and items[0].hotspot_targets is not None:
        hotspot_targets = torch.tensor([item.hotspot_targets for item in items], dtype=torch.float32)
    if sequence_node_tensor.ndim == 3:
        sequence_node_tensor = sequence_node_tensor.view(batch_size, step_count, node_count, node_feature_count)
    if sequence_signal_tensor.ndim == 2:
        sequence_signal_tensor = sequence_signal_tensor.view(batch_size, step_count, signal_feature_count)
    if node_physics_tensor.ndim == 2:
        node_physics_tensor = node_physics_tensor.view(batch_size, node_count, node_physics_count)
    if global_physics_tensor.ndim == 1:
        global_physics_tensor = global_physics_tensor.view(batch_size, global_physics_count)
    return MainModelInputBundle(
        sequence_node_features=_select_and_normalize(sequence_node_tensor, transforms.node_features),
        sequence_global_signal_features=_select_and_normalize(sequence_signal_tensor, transforms.global_signal_features),
        node_physics_features=_select_and_normalize(node_physics_tensor, transforms.node_physics_features),
        global_physics_features=_select_and_normalize(global_physics_tensor, transforms.global_physics_features),
        physics_quality_mask=torch.tensor([item.physics_quality_mask for item in items], dtype=torch.float32),
        adjacency=torch.tensor([item.adjacency for item in items], dtype=torch.float32),
        regression_targets=torch.tensor([item.regression_targets for item in items], dtype=torch.float32),
        hotspot_targets=hotspot_targets,
        observed_mask=torch.tensor([item.observed_mask for item in items], dtype=torch.bool),
        physics_baseline=torch.tensor([item.physics_baseline for item in items], dtype=torch.float32),
        metadata=[[dict(row) for row in item.metadata] for item in items],
    )


def _build_loader(examples: list[TemporalGraphSequenceExample], batch_size: int, shuffle: bool, transforms: FeatureTransformBundle) -> DataLoader[Any]:
    return DataLoader(
        TemporalSequenceDataset(examples),
        batch_size=max(1, batch_size),
        shuffle=shuffle,
        collate_fn=lambda items: _collate_temporal_examples(items, transforms),
    )


def _sigmoid(values: torch.Tensor | None) -> torch.Tensor | None:
    if values is None:
        return None
    return torch.sigmoid(values)


def prediction_rows_from_main_output(output: MainModelOutputBundle) -> list[dict[str, Any]]:
    predictions = output.regression_prediction.detach().cpu().tolist()
    targets = output.regression_target.detach().cpu().tolist()
    observed = output.observed_mask.detach().cpu().tolist()
    physics_baseline = output.physics_baseline.detach().cpu().tolist()
    hotspot_probabilities = _sigmoid(output.hotspot_logits)
    hotspot_probability_values = hotspot_probabilities.detach().cpu().tolist() if hotspot_probabilities is not None else None
    hotspot_targets = output.hotspot_target.detach().cpu().tolist() if output.hotspot_target is not None else None
    risk_scores = output.risk_score.detach().cpu().tolist() if output.risk_score is not None else None
    uncertainties = output.uncertainty.detach().cpu().tolist() if output.uncertainty is not None else None
    rows: list[dict[str, Any]] = []
    for batch_index, metadata_rows in enumerate(output.metadata):
        for node_index, metadata in enumerate(metadata_rows):
            row = dict(metadata)
            prediction = float(predictions[batch_index][node_index])
            target = float(targets[batch_index][node_index])
            row.update(
                {
                    'prediction': prediction,
                    'target': target,
                    'observed': bool(observed[batch_index][node_index]),
                    'physics_baseline': float(physics_baseline[batch_index][node_index]),
                    'absolute_error': abs(prediction - target),
                }
            )
            if hotspot_probability_values is not None:
                probability = float(hotspot_probability_values[batch_index][node_index])
                row['hotspot_probability'] = probability
                row['hotspot_prediction'] = bool(probability >= 0.5)
            if hotspot_targets is not None:
                row['hotspot_target'] = float(hotspot_targets[batch_index][node_index])
            if risk_scores is not None:
                row['risk_score'] = float(risk_scores[batch_index][node_index])
            if uncertainties is not None:
                row['uncertainty'] = float(uncertainties[batch_index][node_index])
            rows.append(row)
    return rows


def prediction_rows_from_main_outputs(outputs: list[MainModelOutputBundle]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for output in outputs:
        rows.extend(prediction_rows_from_main_output(output))
    return rows


def _mean_component(history_rows: list[dict[str, float]]) -> dict[str, float]:
    if not history_rows:
        return {}
    keys = sorted({key for row in history_rows for key in row})
    return {
        key: sum(float(row.get(key, 0.0)) for row in history_rows) / len(history_rows)
        for key in keys
    }


def _selection_score(metrics: dict[str, Any]) -> float:
    hidden_count = int(metrics.get('hidden_row_count', 0))
    if hidden_count > 0:
        return float(metrics.get('hidden_only', {}).get('mae', metrics.get('overall', {}).get('mae', math.inf)))
    return float(metrics.get('overall', {}).get('mae', math.inf))


def _run_training_epoch(model: nn.Module, loader: DataLoader[Any], optimizer: Adam, composer: LossComposer, device: torch.device) -> dict[str, float]:
    model.train()
    batch_components: list[dict[str, float]] = []
    for batch in loader:
        main_batch = batch.to(device)
        optimizer.zero_grad()
        output = model(main_batch)
        loss_payload = composer(output)
        loss_payload.total.backward()
        optimizer.step()
        batch_components.append({key: float(value.detach().cpu().item()) for key, value in loss_payload.components.items()})
    return _mean_component(batch_components)


def _run_inference(model: nn.Module, loader: DataLoader[Any], device: torch.device) -> list[MainModelOutputBundle]:
    model.eval()
    outputs: list[MainModelOutputBundle] = []
    with torch.no_grad():
        for batch in loader:
            main_batch = batch.to(device)
            outputs.append(model.predict_batch(main_batch))
    return outputs


def _empty_metrics() -> dict[str, Any]:
    return {
        'row_count': 0,
        'hidden_row_count': 0,
        'observed_row_count': 0,
        'overall': {'mae': 0.0, 'rmse': 0.0, 'correlation': 0.0, 'nmae': 0.0},
        'hidden_only': {'mae': 0.0, 'rmse': 0.0, 'correlation': 0.0, 'nmae': 0.0},
        'observed_only': {'mae': 0.0, 'rmse': 0.0, 'correlation': 0.0, 'nmae': 0.0},
    }


def _feature_transform_summary(transforms: FeatureTransformBundle) -> dict[str, Any]:
    return transforms.feature_summary()


def _signal_summary(examples: list[TemporalGraphSequenceExample], transforms: FeatureTransformBundle) -> dict[str, Any]:
    quality_counts: Counter[str] = Counter()
    for item in examples:
        for flag in item.quality_flags:
            quality_counts[str(flag)] += 1
    return {
        'active_feature_count': transforms.global_signal_features.dim,
        'active_feature_names': list(transforms.global_signal_features.active_names),
        'dropped_zero_variance_count': len(transforms.global_signal_features.dropped_zero_variance),
        'dropped_zero_variance': list(transforms.global_signal_features.dropped_zero_variance),
        'quality_flag_counts': dict(sorted(quality_counts.items())),
    }


def _dataset_summary(dataset_path: str | Path) -> dict[str, Any]:
    dataset = GraphDataset.from_path(dataset_path)
    samples = dataset.load_samples()
    scenario_ids = [str(sample.scenario_id) for sample in samples if str(sample.scenario_id)]
    scenario_to_splits: dict[str, set[str]] = {}
    graph_to_scenario = {sample.graph_id: str(sample.scenario_id) for sample in samples}
    for split_name, graph_ids in dataset.split_assignments.items():
        for graph_id in graph_ids:
            scenario_id = graph_to_scenario.get(graph_id, '')
            if not scenario_id:
                continue
            scenario_to_splits.setdefault(scenario_id, set()).add(split_name)
    scenario_grouped_split = all(len(splits) <= 1 for splits in scenario_to_splits.values())
    return {
        'graph_count': len(dataset.graph_paths),
        'scenario_count': len(set(scenario_ids)),
        'train_graph_count': len(dataset.split_assignments.get('train', [])),
        'val_graph_count': len(dataset.split_assignments.get('val', [])),
        'test_graph_count': len(dataset.split_assignments.get('test', [])),
        'scenario_grouped_split': scenario_grouped_split,
    }


def train_main_model(
    *,
    config: dict[str, Any],
    dataset_path: str | Path,
    output_dir: str | Path,
) -> MainModelTrainingResult:
    training_cfg = dict(config.get('training', {}))
    task_cfg = dict(config.get('task', {}))
    temporal_cfg = dict(config.get('temporal', {}))
    target_level = str(task_cfg.get('target_level', 'bus'))
    seed = int(training_cfg.get('seed', 42))
    batch_size = int(training_cfg.get('batch_size', 8))
    epochs = int(training_cfg.get('epochs', 40))
    learning_rate = float(training_cfg.get('lr', 1e-3))
    weight_decay = float(training_cfg.get('weight_decay', 0.0))
    window_size = int(temporal_cfg.get('window_size', 3))
    hotspot_quantile = float(temporal_cfg.get('hotspot_quantile', 0.75))
    physics_feature_name = str(temporal_cfg.get('physics_feature_name', 'physics.adjacent_induced_abs_sum'))

    _set_seed(seed)
    dataset_path = str(Path(dataset_path).resolve())
    train_examples = load_temporal_graph_examples(dataset_path, split='train', target_level=target_level, window_size=window_size, hotspot_quantile=hotspot_quantile, physics_feature_name=physics_feature_name)
    val_examples = load_temporal_graph_examples(dataset_path, split='val', target_level=target_level, window_size=window_size, hotspot_quantile=hotspot_quantile, physics_feature_name=physics_feature_name)
    test_examples = load_temporal_graph_examples(dataset_path, split='test', target_level=target_level, window_size=window_size, hotspot_quantile=hotspot_quantile, physics_feature_name=physics_feature_name)
    if not train_examples:
        raise ValueError(f'Train split is empty for temporal examples: {dataset_path}')
    if not val_examples:
        raise ValueError(f'Validation split is empty for temporal examples: {dataset_path}')

    transforms = _prepare_feature_transforms(train_examples, config)
    active_feature_names = transforms.combined_active_feature_names()
    input_dims = transforms.model_input_dims()
    model = build_main_model(
        config,
        node_input_dim=input_dims['node_input_dim'],
        global_signal_dim=input_dims['global_signal_dim'],
        node_physics_dim=input_dims['node_physics_dim'],
        global_physics_dim=input_dims['global_physics_dim'],
    )
    composer = LossComposer(config)
    device = torch.device('cpu')
    model.to(device)
    composer.to(device)
    optimizer = Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)

    train_loader = _build_loader(train_examples, batch_size=batch_size, shuffle=True, transforms=transforms)
    val_loader = _build_loader(val_examples, batch_size=batch_size, shuffle=False, transforms=transforms)
    test_loader = _build_loader(test_examples, batch_size=batch_size, shuffle=False, transforms=transforms) if test_examples else None

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_root / 'phase5_main_best.pt'
    history_path = output_root / 'phase5_main_training_history.json'

    feature_summary = _feature_transform_summary(transforms)
    signal_summary = _signal_summary(train_examples, transforms)
    dataset_summary = _dataset_summary(dataset_path)

    history: list[dict[str, Any]] = []
    best_epoch = 0
    best_score = math.inf
    best_metrics = _empty_metrics()
    best_hotspot_metrics = {'row_count': 0, 'threshold': 0.5, 'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'positive_rate': 0.0}
    for epoch in range(1, epochs + 1):
        composer.set_epoch(epoch)
        train_loss_components = _run_training_epoch(model, train_loader, optimizer, composer, device)
        val_outputs = _run_inference(model, val_loader, device)
        val_rows = prediction_rows_from_main_outputs(val_outputs)
        val_metrics = summarize_prediction_rows(val_rows)
        val_hotspot_metrics = summarize_hotspot_rows(val_rows)
        score = _selection_score(val_metrics)
        history.append(
            {
                'epoch': epoch,
                'train_loss_components': train_loss_components,
                'validation_metrics': val_metrics,
                'validation_hotspot_metrics': val_hotspot_metrics,
                'selection_score': score,
                'active_feature_names': active_feature_names,
            }
        )
        if score <= best_score:
            best_score = score
            best_epoch = epoch
            best_metrics = val_metrics
            best_hotspot_metrics = val_hotspot_metrics
            save_checkpoint(
                checkpoint_path,
                model=model,
                optimizer=optimizer,
                epoch=epoch,
                metadata={
                    'dataset_path': dataset_path,
                    'input_dim': input_dims['node_input_dim'],
                    'active_feature_names': active_feature_names,
                    'feature_transforms': transforms.to_metadata(),
                    'feature_summary': feature_summary,
                    'signal_summary': signal_summary,
                    'dataset_summary': dataset_summary,
                    'model_input_dims': input_dims,
                    'target_level': target_level,
                    'training_config': training_cfg,
                    'model_config': dict(config.get('model', {})),
                    'task_config': dict(config.get('tasks', {})),
                    'temporal_config': temporal_cfg,
                },
            )

    write_json_report(history, history_path)
    load_checkpoint(checkpoint_path, model=model, map_location='cpu')
    test_metrics = _empty_metrics()
    test_hotspot_metrics = {'row_count': 0, 'threshold': 0.5, 'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'positive_rate': 0.0}
    if test_loader is not None:
        test_outputs = _run_inference(model, test_loader, device)
        test_rows = prediction_rows_from_main_outputs(test_outputs)
        test_metrics = summarize_prediction_rows(test_rows)
        test_hotspot_metrics = summarize_hotspot_rows(test_rows)

    return MainModelTrainingResult(
        dataset_path=dataset_path,
        checkpoint_path=str(checkpoint_path),
        history_path=str(history_path),
        best_epoch=best_epoch,
        input_dim=input_dims['node_input_dim'],
        feature_names=active_feature_names,
        feature_summary=feature_summary,
        signal_summary=signal_summary,
        dataset_summary=dataset_summary,
        model_input_dims=input_dims,
        train_example_count=len(train_examples),
        val_example_count=len(val_examples),
        test_example_count=len(test_examples),
        validation_metrics=best_metrics,
        validation_hotspot_metrics=best_hotspot_metrics,
        test_metrics=test_metrics,
        test_hotspot_metrics=test_hotspot_metrics,
    )


def _legacy_transforms(examples: list[TemporalGraphSequenceExample], config: dict[str, Any]) -> FeatureTransformBundle:
    return _prepare_feature_transforms(examples, config)


def _checkpoint_metadata(checkpoint_path: str | Path) -> dict[str, Any]:
    payload = torch.load(Path(checkpoint_path), map_location='cpu')
    return dict(payload.get('metadata', {}))


def evaluate_main_model(
    *,
    config: dict[str, Any],
    dataset_path: str | Path,
    checkpoint_path: str | Path,
    split: str = 'test',
) -> dict[str, Any]:
    training_cfg = dict(config.get('training', {}))
    task_cfg = dict(config.get('task', {}))
    temporal_cfg = dict(config.get('temporal', {}))
    evaluation_cfg = dict(config.get('evaluation', {}))
    target_level = str(task_cfg.get('target_level', 'bus'))
    batch_size = int(training_cfg.get('batch_size', 8))
    window_size = int(temporal_cfg.get('window_size', 3))
    hotspot_quantile = float(temporal_cfg.get('hotspot_quantile', 0.75))
    physics_feature_name = str(temporal_cfg.get('physics_feature_name', 'physics.adjacent_induced_abs_sum'))
    hotspot_threshold = float(evaluation_cfg.get('hotspot_threshold', 0.5))

    examples = load_temporal_graph_examples(
        dataset_path,
        split=split,
        target_level=target_level,
        window_size=window_size,
        hotspot_quantile=hotspot_quantile,
        physics_feature_name=physics_feature_name,
    )
    if not examples:
        raise ValueError(f'Split {split} is empty for temporal examples: {dataset_path}')

    checkpoint_payload = torch.load(Path(checkpoint_path), map_location='cpu')
    checkpoint_metadata = dict(checkpoint_payload.get('metadata', {}))
    transforms_payload = checkpoint_metadata.get('feature_transforms')
    transforms = FeatureTransformBundle.from_metadata(dict(transforms_payload)) if isinstance(transforms_payload, dict) else _legacy_transforms(examples, config)
    input_dims = transforms.model_input_dims()
    model = build_main_model(
        config,
        node_input_dim=input_dims['node_input_dim'],
        global_signal_dim=input_dims['global_signal_dim'],
        node_physics_dim=input_dims['node_physics_dim'],
        global_physics_dim=input_dims['global_physics_dim'],
    )
    model.load_state_dict(checkpoint_payload['model_state'])
    device = torch.device('cpu')
    model.to(device)
    loader = _build_loader(examples, batch_size=batch_size, shuffle=False, transforms=transforms)
    outputs = _run_inference(model, loader, device)
    rows = prediction_rows_from_main_outputs(outputs)
    metrics = summarize_prediction_rows(rows)
    hotspot_metrics = summarize_hotspot_rows(rows, threshold=hotspot_threshold)
    return {
        'dataset_path': str(Path(dataset_path).resolve()),
        'checkpoint_path': str(Path(checkpoint_path).resolve()),
        'split': split,
        'row_count': len(rows),
        'active_feature_names': transforms.combined_active_feature_names(),
        'feature_summary': checkpoint_metadata.get('feature_summary', transforms.feature_summary()),
        'signal_summary': checkpoint_metadata.get('signal_summary', _signal_summary(examples, transforms)),
        'dataset_summary': checkpoint_metadata.get('dataset_summary', _dataset_summary(dataset_path)),
        'rows': rows,
        'metrics': metrics,
        'hotspot_metrics': hotspot_metrics,
        'reconstruction_maps': build_reconstruction_maps(rows),
        'case_studies': build_case_studies(rows, top_k=int(evaluation_cfg.get('case_study_top_k', 3))),
    }
