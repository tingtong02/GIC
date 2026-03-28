from __future__ import annotations

import json
from pathlib import Path

from gic.cli.main import main


ROOT = Path(__file__).resolve().parents[1]
PHASE6_CONFIG = ROOT / 'configs/phase6/phase6_dev.yaml'


def test_kg_build_graph_outputs_bundle_paths(capsys) -> None:
    exit_code = main(['kg-build-graph', '--config', str(PHASE6_CONFIG), '--project-root', str(ROOT)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert Path(payload['paths']['entities']).exists()
    assert Path(payload['paths']['relations']).exists()
    assert payload['entity_count'] >= 10


def test_kg_build_report_and_ablation_outputs_reports(capsys) -> None:
    report_exit = main(['kg-build-report', '--config', str(PHASE6_CONFIG), '--project-root', str(ROOT)])
    report_captured = capsys.readouterr()
    report_payload = json.loads(report_captured.out)
    assert report_exit == 0
    assert Path(report_payload['report_path']).exists()
    assert Path(report_payload['markdown_path']).exists()

    ablation_exit = main(['kg-run-ablation', '--config', str(PHASE6_CONFIG), '--project-root', str(ROOT)])
    ablation_captured = capsys.readouterr()
    ablation_payload = json.loads(ablation_captured.out)
    assert ablation_exit == 0
    assert Path(ablation_payload['report_path']).exists()
    assert ablation_payload['ablation_count'] == 3
