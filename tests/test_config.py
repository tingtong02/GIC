from __future__ import annotations

import json
from pathlib import Path

import pytest

from gic.config import ConfigValidationError, dump_config, load_config


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/phase0/phase0_dev.yaml"


def test_load_config_merges_defaults() -> None:
    config = load_config(CONFIG)
    assert config["project"]["name"] == "gic"
    assert config["project"]["stage"] == "phase_0"
    assert config["project"]["profile"] == "phase0_dev"
    assert config["paths"]["artifacts_root"] == "artifacts/runs"


def test_dump_config_is_json_compatible() -> None:
    dumped = dump_config(load_config(CONFIG))
    payload = json.loads(dumped)
    assert payload["runtime"]["mode"] == "dry_run"


def test_missing_required_field_raises(tmp_path: Path) -> None:
    broken = tmp_path / "broken.yaml"
    broken.write_text('{"project": {"name": "gic"}}\n', encoding="utf-8")
    with pytest.raises(ConfigValidationError):
        load_config(broken)
