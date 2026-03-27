from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.training.main_loops import evaluate_main_model, train_main_model


ROOT = Path(__file__).resolve().parents[1]
PHASE5_CONFIG = ROOT / 'configs/phase5/phase5_dev.yaml'
DATASET_PATH = ROOT / 'data/processed/graph_ready/datasets/timeseries_case118_graph_default.json'


def test_train_and_evaluate_phase5_main_model_on_graph_ready_dataset(tmp_path: Path) -> None:
    config = load_config(PHASE5_CONFIG)
    config['training']['epochs'] = 3
    config['training']['batch_size'] = 1
    config['evaluation']['case_study_top_k'] = 2

    train_result = train_main_model(config=config, dataset_path=DATASET_PATH, output_dir=tmp_path / 'train_run')
    assert Path(train_result.checkpoint_path).exists()
    assert Path(train_result.history_path).exists()
    assert train_result.validation_metrics['overall']['mae'] >= 0.0

    eval_result = evaluate_main_model(
        config=config,
        dataset_path=DATASET_PATH,
        checkpoint_path=train_result.checkpoint_path,
        split='test',
    )
    assert eval_result['metrics']['overall']['mae'] >= 0.0
    assert eval_result['hotspot_metrics']['row_count'] > 0
    assert len(eval_result['rows']) > 0
    assert len(eval_result['case_studies']) > 0
