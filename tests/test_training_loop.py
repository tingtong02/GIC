from __future__ import annotations

from pathlib import Path

import pytest

from gic.config import load_config
from gic.graph import build_graph_samples_from_config, build_split_assignments, export_graph_dataset, export_graph_samples
from gic.training import evaluate_baseline_model, train_baseline_model


ROOT = Path(__file__).resolve().parents[1]
PHASE4_CONFIG = ROOT / 'configs/phase4/phase4_dev.yaml'


@pytest.mark.parametrize('model_type', ['mlp', 'gcn', 'graphsage', 'gat'])
def test_train_and_evaluate_phase4_baselines_on_graph_ready_dataset(tmp_path: Path, model_type: str) -> None:
    config = load_config(PHASE4_CONFIG)
    config['training']['epochs'] = 3
    config['training']['batch_size'] = 4
    _, build_context, samples = build_graph_samples_from_config(ROOT, config)
    split_assignments = build_split_assignments([item.graph_id for item in samples], config['graph']['split'])
    manifest, _ = export_graph_samples(
        project_root=tmp_path,
        graph_config=config['graph'],
        dataset_name=build_context['dataset_name'],
        source_case_id=build_context['source_case_id'],
        scenario_id=build_context['scenario_id'],
        task_payload=build_context['task'],
        graph_samples=samples,
        split_assignments=split_assignments,
    )
    dataset_path = export_graph_dataset(project_root=tmp_path, graph_config=config['graph'], manifest=manifest)

    train_result = train_baseline_model(model_type=model_type, config=config, dataset_path=dataset_path, output_dir=tmp_path / 'train_run' / model_type)
    assert Path(train_result.checkpoint_path).exists()
    assert Path(train_result.history_path).exists()
    assert train_result.train_example_count > 0
    assert train_result.validation_metrics['overall']['mae'] >= 0.0

    eval_result = evaluate_baseline_model(
        model_type=model_type,
        config=config,
        dataset_path=dataset_path,
        checkpoint_path=train_result.checkpoint_path,
        split='test',
    )
    assert eval_result['metrics']['overall']['mae'] >= 0.0
    assert len(eval_result['rows']) > 0
    assert len(eval_result['reconstruction_maps']) > 0
