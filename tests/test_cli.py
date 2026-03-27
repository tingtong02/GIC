from __future__ import annotations

import json
from pathlib import Path

from gic.cli.main import main


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/phase0/phase0_dev.yaml"


def test_show_config_outputs_json(capsys) -> None:
    exit_code = main(["show-config", "--config", str(CONFIG)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["project"]["stage"] == "phase_0"


def test_validate_env_outputs_summary(capsys) -> None:
    exit_code = main(["validate-env"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert "python_version" in payload


def test_run_creates_summary(tmp_path: Path, capsys) -> None:
    exit_code = main(
        [
            "run",
            "--config",
            str(CONFIG),
            "--project-root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    summary_path = Path(payload["summary_path"])
    assert exit_code == 0
    assert summary_path.exists()
    assert "Phase 0 dry run completed" in captured.err
