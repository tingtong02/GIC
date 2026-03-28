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
    assert 'global_kg_features' in train_result.feature_summary
    assert 'node_kg_features' in train_result.feature_summary

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


def test_phase6_config_trains_with_kg_features_enabled(tmp_path: Path) -> None:
    phase6_config_path = ROOT / 'configs/phase6/phase6_dev.yaml'
    config = load_config(phase6_config_path)
    config['training']['epochs'] = 1
    config['training']['batch_size'] = 1
    config['ablation']['training_epochs'] = 1

    train_result = train_main_model(
        config=config,
        dataset_path=BROAD_DATASET_PATH,
        output_dir=tmp_path / 'phase6_train_run',
        project_root=ROOT,
    )
    assert Path(train_result.checkpoint_path).exists()
    assert train_result.kg_summary['enabled'] is True
    assert train_result.kg_summary['active_global_feature_count'] >= 1
    assert train_result.kg_summary['feature_group_flags']['topology_context'] is True


def test_phase6_rule_dense_activates_non_constant_rule_features(tmp_path: Path) -> None:
    config = load_config(ROOT / 'configs/phase6/models/kg_default_full.yaml')
    config['training']['epochs'] = 1
    config['training']['batch_size'] = 1

    train_result = train_main_model(
        config=config,
        dataset_path=BROAD_DATASET_PATH,
        output_dir=tmp_path / 'phase6_rule_dense_train',
        project_root=ROOT,
    )
    active_rule_features = list(train_result.kg_summary['rule_variance_summary']['active_rule_features'])
    assert len(active_rule_features) >= 1


def test_phase6_relation_light_activates_relation_features(tmp_path: Path) -> None:
    config = load_config(ROOT / 'configs/phase6/models/relation_light_h64_lr1e3_g005_d00.yaml')
    config['training']['epochs'] = 1
    config['training']['batch_size'] = 1

    train_result = train_main_model(
        config=config,
        dataset_path=BROAD_DATASET_PATH,
        output_dir=tmp_path / 'phase6_relation_light_train',
        project_root=ROOT,
    )
    assert train_result.kg_summary['configured_use_relation_light'] is True
    relation_feature_total = (
        int(train_result.kg_summary['active_relation_global_feature_count'])
        + int(train_result.kg_summary['active_relation_node_feature_count'])
    )
    assert relation_feature_total >= 1
