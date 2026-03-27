from __future__ import annotations

import json
from pathlib import Path

from gic.cli.main import main
from gic.config import load_config


ROOT = Path(__file__).resolve().parents[1]
PHASE5_CONFIG = ROOT / 'configs/phase5/phase5_dev.yaml'
DATASET_PATH = ROOT / 'data/processed/graph_ready/datasets/timeseries_case118_graph_default.json'


def _write_phase5_test_config(tmp_path: Path, *, train_epochs: int = 3, ablation_epochs: int = 2) -> Path:
    config = load_config(PHASE5_CONFIG)
    config['training']['epochs'] = train_epochs
    config['training']['batch_size'] = 1
    config['ablation']['training_epochs'] = ablation_epochs
    for variant in config['ablation']['variants']:
        variant['config_path'] = str((ROOT / 'configs' / 'phase5' / variant['config_path']).resolve())
    config_path = tmp_path / 'phase5_test_config.json'
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return config_path


def test_train_main_model_outputs_checkpoint(tmp_path: Path, capsys) -> None:
    config_path = _write_phase5_test_config(tmp_path)
    exit_code = main(
        [
            'train-main-model',
            '--config',
            str(config_path),
            '--project-root',
            str(ROOT),
            '--dataset-path',
            str(DATASET_PATH),
            '--epochs',
            '3',
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert Path(payload['checkpoint_path']).exists()
    assert Path(payload['history_path']).exists()


def test_build_main_report_outputs_ablation_and_phase4_comparison(tmp_path: Path, capsys) -> None:
    config_path = _write_phase5_test_config(tmp_path, train_epochs=3, ablation_epochs=2)
    exit_code = main(
        [
            'build-main-report',
            '--config',
            str(config_path),
            '--project-root',
            str(ROOT),
            '--dataset-path',
            str(DATASET_PATH),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert Path(payload['report_path']).exists()
    assert Path(payload['markdown_path']).exists()
    assert payload['ablation_count'] == 4
    assert 'phase5_beats_phase4_best' in payload['comparison_with_phase4']
