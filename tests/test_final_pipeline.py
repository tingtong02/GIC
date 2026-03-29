from __future__ import annotations

import json
from pathlib import Path

from gic.cli.main import main
from gic.config import load_config
from gic.pipelines.final_pipeline import run_final_pipeline


ROOT = Path(__file__).resolve().parents[1]
FINAL_CONFIG = ROOT / 'configs/final/final_default.yaml'


def test_run_final_pipeline_check_only_uses_frozen_default() -> None:
    config = load_config(FINAL_CONFIG)
    report = run_final_pipeline(project_root=ROOT, config=config, check_only=True)
    assert report['default_variant'] == 'without_kg'
    assert report['default_model_id'] == 'phase5_default'
    assert report['phase7_default_promotion_decision'] == 'phase5_default_real_event_leader'
    assert report['asset_check']
    assert report['phase7_failure_cases']


def test_build_final_report_cli_exports_summary(tmp_path: Path, capsys) -> None:
    exit_code = main([
        'build-final-report',
        '--config',
        str(FINAL_CONFIG),
        '--project-root',
        str(ROOT),
        '--output-dir',
        str(tmp_path),
        '--check-only',
    ])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert Path(payload['summary_json_path']).exists()
    assert Path(payload['summary_markdown_path']).exists()
    summary = json.loads(Path(payload['summary_json_path']).read_text(encoding='utf-8'))
    assert summary['default_variant'] == 'without_kg'
