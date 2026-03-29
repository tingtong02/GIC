from __future__ import annotations

import json
from pathlib import Path

from gic.cli.main import main


ROOT = Path(__file__).resolve().parents[1]
FINAL_CONFIG = ROOT / 'configs/final/final_default.yaml'


def test_export_final_visuals_cli_outputs_expected_svgs(tmp_path: Path, capsys) -> None:
    exit_code = main([
        'export-final-visuals',
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
    assert Path(payload['synthetic_model_comparison_svg']).exists()
    assert Path(payload['real_model_comparison_svg']).exists()
    assert Path(payload['network_map_svg']).exists()
    assert Path(payload['timeline_svg']).exists()
    assert Path(payload['failure_cases_svg']).exists()
    assert Path(payload['kg_view_svg']).exists()
    manifest = json.loads(Path(payload['visual_manifest_path']).read_text(encoding='utf-8'))
    assert 'kg_view_svg' in manifest
