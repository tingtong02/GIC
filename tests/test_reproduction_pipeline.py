from __future__ import annotations

import json
from pathlib import Path

from gic.cli.main import main


ROOT = Path(__file__).resolve().parents[1]
FINAL_CONFIG = ROOT / 'configs/final/final_reproduction.yaml'


def test_run_final_reproduction_cli_exports_bundle(tmp_path: Path, capsys) -> None:
    exit_code = main([
        'run-final-reproduction',
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
    assert Path(payload['casebook_json_path']).exists()
    assert Path(payload['casebook_markdown_path']).exists()
    assert Path(payload['doc_summary_path']).exists()
    assert Path(payload['visual_manifest_path']).exists()
