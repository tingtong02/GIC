from __future__ import annotations

import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader, Dataset

from gic.eval import build_reconstruction_maps, summarize_prediction_rows
from gic.eval.case_studies import build_case_studies
from gic.eval.hotspot_metrics import summarize_hotspot_rows
from gic.eval.reporting import write_json_report
from gic.graph.datasets import TemporalGraphSequenceExample, load_temporal_graph_examples
from gic.losses import LossComposer
from gic.models import MainModelInputBundle, MainModelOutputBundle, build_main_model
from gic.training.checkpoint import load_checkpoint, save_checkpoint


@dataclass(slots=True)
class MainModelTrainingResult:
    dataset_path: str
    checkpoint_path: str
    history_path: str
    best_epoch: int
    input_dim: int
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



def _collate_temporal_examples(items: list[TemporalGraphSequenceExample]) -> MainModelInputBundle:
    hotspot_targets = None
    if items and items[0].hotspot_targets is not None:
        hotspot_targets = torch.tensor([item.hotspot_targets for item in items], dtype=torch.float32)
    return MainModelInputBundle(
        sequence_features=torch.tensor([item.sequence_features for item in items], dtype=torch.float32),
        adjacency=torch.tensor([item.adjacency for item in items], dtype=torch.float32),
        regression_targets=torch.tensor([item.regression_targets for item in items], dtype=torch.float32),
        hotspot_targets=hotspot_targets,
        observed_mask=torch.tensor([item.observed_mask for item in items], dtype=torch.bool),
        physics_baseline=torch.tensor([item.physics_baseline for item in items], dtype=torch.float32),
        metadata=[[dict(row) for row in item.metadata] for item in items],
    )



def _build_loader(examples: list[TemporalGraphSequenceExample], batch_size: int, shuffle: bool) -> DataLoader[Any]:
    return DataLoader(
        TemporalSequenceDataset(examples),
        batch_size=max(1, batch_size),
        shuffle=shuffle,
        collate_fn=_collate_temporal_examples,
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
        'overall': {'mae': 0.0, 'rmse': 0.0, 'correlation': 0.0},
        'hidden_only': {'mae': 0.0, 'rmse': 0.0, 'correlation': 0.0},
        'observed_only': {'mae': 0.0, 'rmse': 0.0, 'correlation': 0.0},
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

    input_dim = len(train_examples[0].sequence_features[0][0])
    model = build_main_model(config, input_dim=input_dim)
    composer = LossComposer(config)
    device = torch.device('cpu')
    model.to(device)
    composer.to(device)
    optimizer = Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)

    train_loader = _build_loader(train_examples, batch_size=batch_size, shuffle=True)
    val_loader = _build_loader(val_examples, batch_size=batch_size, shuffle=False)
    test_loader = _build_loader(test_examples, batch_size=batch_size, shuffle=False) if test_examples else None

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_root / 'phase5_main_best.pt'
    history_path = output_root / 'phase5_main_training_history.json'

    history: list[dict[str, Any]] = []
    best_epoch = 0
    best_score = math.inf
    best_metrics = _empty_metrics()
    best_hotspot_metrics = {'row_count': 0, 'threshold': 0.5, 'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0, 'positive_rate': 0.0}
    for epoch in range(1, epochs + 1):
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
                    'input_dim': input_dim,
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
        input_dim=input_dim,
        train_example_count=len(train_examples),
        val_example_count=len(val_examples),
        test_example_count=len(test_examples),
        validation_metrics=best_metrics,
        validation_hotspot_metrics=best_hotspot_metrics,
        test_metrics=test_metrics,
        test_hotspot_metrics=test_hotspot_metrics,
    )



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
    input_dim = len(examples[0].sequence_features[0][0])
    model = build_main_model(config, input_dim=input_dim)
    load_checkpoint(checkpoint_path, model=model, map_location='cpu')
    device = torch.device('cpu')
    model.to(device)
    loader = _build_loader(examples, batch_size=batch_size, shuffle=False)
    outputs = _run_inference(model, loader, device)
    rows = prediction_rows_from_main_outputs(outputs)
    metrics = summarize_prediction_rows(rows)
    hotspot_metrics = summarize_hotspot_rows(rows, threshold=hotspot_threshold)
    return {
        'dataset_path': str(Path(dataset_path).resolve()),
        'checkpoint_path': str(Path(checkpoint_path).resolve()),
        'split': split,
        'row_count': len(rows),
        'rows': rows,
        'metrics': metrics,
        'hotspot_metrics': hotspot_metrics,
        'reconstruction_maps': build_reconstruction_maps(rows),
        'case_studies': build_case_studies(rows, top_k=int(evaluation_cfg.get('case_study_top_k', 3))),
    }
