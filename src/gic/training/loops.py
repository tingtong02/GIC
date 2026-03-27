from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader, Dataset

from gic.eval import build_reconstruction_maps, prediction_rows_from_outputs, summarize_prediction_rows, write_json_report
from gic.graph.datasets import (
    GraphRegressionExample,
    NodeRegressionExample,
    load_graph_regression_examples,
    load_node_regression_examples,
)
from gic.models import (
    BaselineBatch,
    BaselinePrediction,
    build_gat_baseline,
    build_gcn_baseline,
    build_graphsage_baseline,
    build_mlp_baseline,
)
from gic.training.checkpoint import load_checkpoint, save_checkpoint


ModelType = Literal['mlp', 'gcn', 'graphsage', 'gat']


@dataclass(slots=True)
class BaselineTrainingResult:
    model_type: str
    dataset_path: str
    checkpoint_path: str
    history_path: str
    best_epoch: int
    input_dim: int
    train_example_count: int
    val_example_count: int
    test_example_count: int
    validation_metrics: dict[str, Any]
    test_metrics: dict[str, Any]


class NodeExampleDataset(Dataset[NodeRegressionExample]):
    def __init__(self, examples: list[NodeRegressionExample]) -> None:
        self.examples = examples

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> NodeRegressionExample:
        return self.examples[index]


class GraphExampleDataset(Dataset[GraphRegressionExample]):
    def __init__(self, examples: list[GraphRegressionExample]) -> None:
        self.examples = examples

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> GraphRegressionExample:
        return self.examples[index]



def _collate_node_examples(items: list[NodeRegressionExample]) -> BaselineBatch:
    return BaselineBatch(
        features=torch.tensor([item.features for item in items], dtype=torch.float32),
        targets=torch.tensor([item.target for item in items], dtype=torch.float32),
        observed_mask=torch.tensor([item.observed for item in items], dtype=torch.bool),
        metadata=[dict(item.metadata) for item in items],
    )



def _collate_graph_examples(items: list[GraphRegressionExample]) -> BaselineBatch:
    feature_tensors = [torch.tensor(item.features, dtype=torch.float32) for item in items]
    target_tensors = [torch.tensor(item.targets, dtype=torch.float32) for item in items]
    observed_tensors = [torch.tensor(item.observed_mask, dtype=torch.bool) for item in items]
    adjacency_tensors = [torch.tensor(item.adjacency, dtype=torch.float32) for item in items]
    graph_index_parts: list[torch.Tensor] = []
    metadata: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        graph_index_parts.append(torch.full((len(item.node_ids),), index, dtype=torch.long))
        metadata.extend([dict(entry) for entry in item.metadata])
    return BaselineBatch(
        features=torch.cat(feature_tensors, dim=0),
        targets=torch.cat(target_tensors, dim=0),
        observed_mask=torch.cat(observed_tensors, dim=0),
        adjacency=torch.block_diag(*adjacency_tensors),
        graph_index=torch.cat(graph_index_parts, dim=0),
        metadata=metadata,
    )



def _set_seed(seed: int) -> None:
    random.seed(seed)
    torch.manual_seed(seed)



def _build_loader(examples: list[Any], batch_size: int, shuffle: bool, model_type: ModelType) -> DataLoader[Any]:
    dataset: Dataset[Any]
    collate_fn: Any
    if model_type == 'mlp':
        dataset = NodeExampleDataset(examples)
        collate_fn = _collate_node_examples
    else:
        dataset = GraphExampleDataset(examples)
        collate_fn = _collate_graph_examples
    return DataLoader(
        dataset,
        batch_size=max(1, batch_size),
        shuffle=shuffle,
        collate_fn=collate_fn,
    )



def _build_examples(dataset_path: str | Path, split: str, target_level: str, model_type: ModelType) -> list[Any]:
    if model_type == 'mlp':
        return load_node_regression_examples(dataset_path, split=split, target_level=target_level)
    return load_graph_regression_examples(dataset_path, split=split, target_level=target_level)



def _build_model(model_type: ModelType, config: dict[str, Any], input_dim: int):
    models_cfg = dict(config.get('models', {}))
    if model_type == 'mlp':
        return build_mlp_baseline(dict(models_cfg.get('mlp', {})), input_dim=input_dim)
    if model_type == 'gcn':
        return build_gcn_baseline(dict(models_cfg.get('gcn', {})), input_dim=input_dim)
    if model_type == 'graphsage':
        return build_graphsage_baseline(dict(models_cfg.get('graphsage', {})), input_dim=input_dim)
    if model_type == 'gat':
        return build_gat_baseline(dict(models_cfg.get('gat', {})), input_dim=input_dim)
    raise ValueError(f'Unsupported model type: {model_type}')



def _model_forward(model: nn.Module, batch: BaselineBatch) -> torch.Tensor:
    return model(
        batch.features,
        adjacency=batch.adjacency,
        graph_index=batch.graph_index,
    )



def _run_training_epoch(model: nn.Module, loader: DataLoader[Any], optimizer: Adam, device: torch.device) -> float:
    model.train()
    loss_fn = nn.MSELoss()
    total_loss = 0.0
    batch_count = 0
    for batch in loader:
        baseline_batch = batch.to(device)
        optimizer.zero_grad()
        predictions = _model_forward(model, baseline_batch)
        loss = loss_fn(predictions, baseline_batch.targets)
        loss.backward()
        optimizer.step()
        total_loss += float(loss.item())
        batch_count += 1
    return total_loss / max(batch_count, 1)



def _run_inference(model: nn.Module, loader: DataLoader[Any], device: torch.device) -> list[BaselinePrediction]:
    model.eval()
    outputs: list[BaselinePrediction] = []
    with torch.no_grad():
        for batch in loader:
            baseline_batch = batch.to(device)
            outputs.append(model.predict_batch(baseline_batch))
    return outputs



def _metric_selection_key(metrics: dict[str, Any]) -> float:
    hidden_only = metrics.get('hidden_only', {})
    hidden_count = int(metrics.get('hidden_row_count', 0))
    if hidden_count > 0:
        return float(hidden_only.get('mae', 0.0))
    return float(metrics.get('overall', {}).get('mae', 0.0))



def train_baseline_model(
    *,
    model_type: ModelType,
    config: dict[str, Any],
    dataset_path: str | Path,
    output_dir: str | Path,
) -> BaselineTrainingResult:
    training_cfg = dict(config.get('training', {}))
    task_cfg = dict(config.get('task', {}))
    target_level = str(task_cfg.get('target_level', 'bus'))
    seed = int(training_cfg.get('seed', 42))
    batch_size = int(training_cfg.get('batch_size', 8))
    epochs = int(training_cfg.get('epochs', 25))
    learning_rate = float(training_cfg.get('lr', 1e-3))
    weight_decay = float(training_cfg.get('weight_decay', 0.0))

    _set_seed(seed)
    dataset_path = str(Path(dataset_path).resolve())
    train_examples = _build_examples(dataset_path, 'train', target_level, model_type)
    val_examples = _build_examples(dataset_path, 'val', target_level, model_type)
    test_examples = _build_examples(dataset_path, 'test', target_level, model_type)
    if not train_examples:
        raise ValueError(f'Train split is empty: {dataset_path}')
    if not val_examples:
        raise ValueError(f'Validation split is empty: {dataset_path}')

    first_example = train_examples[0]
    input_dim = len(first_example.features[0]) if hasattr(first_example, 'features') and first_example.features and isinstance(first_example.features[0], list) else len(first_example.features)
    model = _build_model(model_type, config, input_dim=input_dim)
    device = torch.device('cpu')
    model.to(device)
    optimizer = Adam(model.parameters(), lr=learning_rate, weight_decay=weight_decay)

    train_loader = _build_loader(train_examples, batch_size=batch_size, shuffle=True, model_type=model_type)
    val_loader = _build_loader(val_examples, batch_size=batch_size, shuffle=False, model_type=model_type)
    test_loader = _build_loader(test_examples, batch_size=batch_size, shuffle=False, model_type=model_type) if test_examples else None

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_root / f'{model_type}_best.pt'
    history_path = output_root / f'{model_type}_training_history.json'

    history: list[dict[str, Any]] = []
    best_epoch = 0
    best_score = float('inf')
    best_metrics: dict[str, Any] = {}
    for epoch in range(1, epochs + 1):
        train_loss = _run_training_epoch(model, train_loader, optimizer, device)
        val_outputs = _run_inference(model, val_loader, device)
        val_rows = prediction_rows_from_outputs(val_outputs)
        val_metrics = summarize_prediction_rows(val_rows)
        score = _metric_selection_key(val_metrics)
        history.append(
            {
                'epoch': epoch,
                'train_loss': train_loss,
                'validation_metrics': val_metrics,
                'selection_score': score,
            }
        )
        if score <= best_score:
            best_score = score
            best_epoch = epoch
            best_metrics = val_metrics
            save_checkpoint(
                checkpoint_path,
                model=model,
                optimizer=optimizer,
                epoch=epoch,
                metadata={
                    'model_type': model_type,
                    'dataset_path': dataset_path,
                    'input_dim': input_dim,
                    'target_level': target_level,
                    'training_config': training_cfg,
                    'model_config': dict(config.get('models', {}).get(model_type, {})),
                },
            )

    write_json_report(history, history_path)
    load_checkpoint(checkpoint_path, model=model, map_location='cpu')
    test_metrics = {
        'row_count': 0,
        'hidden_row_count': 0,
        'observed_row_count': 0,
        'overall': {'mae': 0.0, 'rmse': 0.0, 'correlation': 0.0},
        'hidden_only': {'mae': 0.0, 'rmse': 0.0, 'correlation': 0.0},
        'observed_only': {'mae': 0.0, 'rmse': 0.0, 'correlation': 0.0},
    }
    if test_loader is not None:
        test_outputs = _run_inference(model, test_loader, device)
        test_rows = prediction_rows_from_outputs(test_outputs)
        test_metrics = summarize_prediction_rows(test_rows)

    return BaselineTrainingResult(
        model_type=model_type,
        dataset_path=dataset_path,
        checkpoint_path=str(checkpoint_path),
        history_path=str(history_path),
        best_epoch=best_epoch,
        input_dim=input_dim,
        train_example_count=len(train_examples),
        val_example_count=len(val_examples),
        test_example_count=len(test_examples),
        validation_metrics=best_metrics,
        test_metrics=test_metrics,
    )



def evaluate_baseline_model(
    *,
    model_type: ModelType,
    config: dict[str, Any],
    dataset_path: str | Path,
    checkpoint_path: str | Path,
    split: str = 'test',
) -> dict[str, Any]:
    training_cfg = dict(config.get('training', {}))
    task_cfg = dict(config.get('task', {}))
    target_level = str(task_cfg.get('target_level', 'bus'))
    batch_size = int(training_cfg.get('batch_size', 8))
    examples = _build_examples(dataset_path, split, target_level, model_type)
    if not examples:
        raise ValueError(f'Split {split} is empty: {dataset_path}')
    first_example = examples[0]
    input_dim = len(first_example.features[0]) if hasattr(first_example, 'features') and first_example.features and isinstance(first_example.features[0], list) else len(first_example.features)
    model = _build_model(model_type, config, input_dim=input_dim)
    load_checkpoint(checkpoint_path, model=model, map_location='cpu')
    device = torch.device('cpu')
    model.to(device)
    loader = _build_loader(examples, batch_size=batch_size, shuffle=False, model_type=model_type)
    outputs = _run_inference(model, loader, device)
    rows = prediction_rows_from_outputs(outputs)
    metrics = summarize_prediction_rows(rows)
    return {
        'model_type': model_type,
        'dataset_path': str(Path(dataset_path).resolve()),
        'checkpoint_path': str(Path(checkpoint_path).resolve()),
        'split': split,
        'input_dim': input_dim,
        'metrics': metrics,
        'rows': rows,
        'reconstruction_maps': build_reconstruction_maps(rows),
    }



def train_mlp_baseline(*, config: dict[str, Any], dataset_path: str | Path, output_dir: str | Path) -> BaselineTrainingResult:
    return train_baseline_model(model_type='mlp', config=config, dataset_path=dataset_path, output_dir=output_dir)



def evaluate_mlp_baseline(*, config: dict[str, Any], dataset_path: str | Path, checkpoint_path: str | Path, split: str = 'test') -> dict[str, Any]:
    return evaluate_baseline_model(model_type='mlp', config=config, dataset_path=dataset_path, checkpoint_path=checkpoint_path, split=split)
