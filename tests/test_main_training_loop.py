from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.graph import load_temporal_graph_examples
from gic.training.main_loops import evaluate_main_model, train_main_model


ROOT = Path(__file__).resolve().parents[1]
PHASE5_CONFIG = ROOT / 'configs/phase5/phase5_dev.yaml'
DATASET_PATH = ROOT / 'data/processed/graph_ready/datasets/timeseries_case118_graph_default.json'

BROAD_DATASET_PATH = ROOT / 'data/processed/graph_ready/datasets/case118_graph_broader.json'


def test_train_and_evaluate_phase5_main_model_on_graph_ready_dataset(tmp_path: Path) -> None:
    config = load_config(PHASE5_CONFIG)
    config['training']['epochs'] = 3
    config['training']['batch_size'] = 1
    config['evaluation']['case_study_top_k'] = 2

    train_result = train_main_model(config=config, dataset_path=DATASET_PATH, output_dir=tmp_path / 'train_run')
    assert Path(train_result.checkpoint_path).exists()
    assert Path(train_result.history_path).exists()
    assert train_result.validation_metrics['overall']['mae'] >= 0.0
    assert 'global_signal_features' in train_result.feature_summary
    assert 'global_physics_features' in train_result.feature_summary

    eval_result = evaluate_main_model(
        config=config,
        dataset_path=DATASET_PATH,
        checkpoint_path=train_result.checkpoint_path,
        split='test',
    )
    assert eval_result['metrics']['overall']['mae'] >= 0.0
    assert eval_result['metrics']['overall']['nmae'] >= 0.0
    assert eval_result['hotspot_metrics']['row_count'] > 0
    assert len(eval_result['rows']) > 0
    assert len(eval_result['case_studies']) > 0
    assert 'dataset_summary' in eval_result


def test_phase5_feature_switches_change_active_feature_names(tmp_path: Path) -> None:
    config = load_config(PHASE5_CONFIG)
    config['training']['epochs'] = 2
    config['training']['batch_size'] = 1
    config['model']['use_signal_features'] = False
    config['model']['use_physics_features'] = False

    train_result = train_main_model(config=config, dataset_path=DATASET_PATH, output_dir=tmp_path / 'feature_switches')
    assert all(not name.startswith('signal.') for name in train_result.feature_names)
    assert all(not name.startswith('physics.') for name in train_result.feature_names)
    assert train_result.feature_summary['global_signal_features']['active_count'] == 0
    assert train_result.feature_summary['node_physics_features']['active_count'] == 0
    assert train_result.feature_summary['global_physics_features']['active_count'] == 0


def test_broader_dataset_builds_temporal_examples_with_prefix_padding() -> None:
    examples = load_temporal_graph_examples(
        BROAD_DATASET_PATH,
        split='train',
        target_level='bus',
        window_size=3,
        hotspot_quantile=0.75,
        physics_feature_name='physics.adjacent_induced_abs_sum',
    )
    assert len(examples) > 0
    assert len(examples[0].sequence_graph_ids) == 3
