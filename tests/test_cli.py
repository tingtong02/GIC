from __future__ import annotations

import json
from pathlib import Path

from gic.cli.main import main


ROOT = Path(__file__).resolve().parents[1]
PHASE0_CONFIG = ROOT / "configs/phase0/phase0_dev.yaml"
PHASE1_CONFIG = ROOT / "configs/phase1/phase1_dev.yaml"
PHASE3_CONFIG = ROOT / "configs/phase3/phase3_dev.yaml"


def test_show_config_outputs_json(capsys) -> None:
    exit_code = main(["show-config", "--config", str(PHASE0_CONFIG)])
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
            str(PHASE0_CONFIG),
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


def test_data_list_sources_outputs_registry(capsys) -> None:
    exit_code = main(["data-list-sources", "--config", str(PHASE1_CONFIG)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert any(item["source_name"] == "matpower_case118" for item in payload["sources"])


def test_data_convert_sample_writes_interim_outputs(capsys) -> None:
    exit_code = main(
        [
            "data-convert-sample",
            "--config",
            str(PHASE1_CONFIG),
            "--project-root",
            str(ROOT),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["manifest_count"] >= 2


def test_signal_validate_input_outputs_report(capsys) -> None:
    exit_code = main(
        [
            "signal-validate-input",
            "--config",
            str(PHASE3_CONFIG),
            "--project-root",
            str(ROOT),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert Path(payload["report_path"]).exists()


def test_signal_compare_frontends_outputs_default_method(capsys) -> None:
    exit_code = main(
        [
            "signal-compare-frontends",
            "--config",
            str(PHASE3_CONFIG),
            "--project-root",
            str(ROOT),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["comparison_report"]["default_method"] in {
        "raw_baseline",
        "lowfreq_baseline",
        "fastica",
        "sparse_denoise",
    }
