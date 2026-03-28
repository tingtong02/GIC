from __future__ import annotations

import json
from pathlib import Path

from gic.cli.main import main
from gic.config import load_config


ROOT = Path(__file__).resolve().parents[1]
PHASE6_CONFIG = ROOT / 'configs/phase6/phase6_dev.yaml'
DATASET_PATH = ROOT / 'data/processed/graph_ready/datasets/case118_graph_broader.json'


def _write_phase6_test_config(tmp_path: Path, *, train_epochs: int = 2, ablation_epochs: int = 1) -> Path:
    config = load_config(PHASE6_CONFIG)
    config['training']['epochs'] = train_epochs
    config['training']['batch_size'] = 1
    config['ablation']['training_epochs'] = ablation_epochs
    config_path = tmp_path / 'phase6_test_config.json'
    config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return config_path


def test_kg_build_graph_outputs_bundle_paths(capsys, tmp_path: Path) -> None:
    config_path = _write_phase6_test_config(tmp_path)
    exit_code = main(['kg-build-graph', '--config', str(config_path), '--project-root', str(ROOT), '--dataset-path', str(DATASET_PATH)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert Path(payload['paths']['entities']).exists()
    assert Path(payload['paths']['relations']).exists()
    assert payload['entity_count'] >= 10


def test_kg_build_report_and_ablation_outputs_reports(capsys, tmp_path: Path) -> None:
    config_path = _write_phase6_test_config(tmp_path, train_epochs=2, ablation_epochs=1)
    report_exit = main(['kg-build-report', '--config', str(config_path), '--project-root', str(ROOT), '--dataset-path', str(DATASET_PATH)])
    report_captured = capsys.readouterr()
    report_payload = json.loads(report_captured.out)
    assert report_exit == 0
    assert Path(report_payload['report_path']).exists()
    assert Path(report_payload['markdown_path']).exists()
    assert report_payload['recommended_variant'] in {'no_kg', 'feature_only', 'kg_default'}

    report_json = json.loads(Path(report_payload['report_path']).read_text(encoding='utf-8'))
    assert 'surface_results' in report_json
    assert 'default_promotion_decision' in report_json
    assert 'feature_only' in report_json['surface_results']

    ablation_exit = main(['kg-run-ablation', '--config', str(config_path), '--project-root', str(ROOT), '--dataset-path', str(DATASET_PATH)])
    ablation_captured = capsys.readouterr()
    ablation_payload = json.loads(ablation_captured.out)
    assert ablation_exit == 0
    assert Path(ablation_payload['report_path']).exists()
    assert ablation_payload['ablation_count'] == 3
    assert ablation_payload['recommended_variant'] in {'no_kg', 'feature_only', 'kg_default'}
