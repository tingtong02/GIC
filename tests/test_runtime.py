from __future__ import annotations

import json
from pathlib import Path

from gic.config import load_config
from gic.utils.runtime import initialize_run


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/phase0/phase0_dev.yaml"


def test_initialize_run_writes_expected_files(tmp_path: Path) -> None:
    config = load_config(CONFIG)
    context, metadata = initialize_run(
        config=config,
        config_path=str(CONFIG),
        command="run",
        project_root=tmp_path,
    )

    assert context.config_snapshot_path.exists()
    assert context.metadata_path.exists()
    assert context.artifact_dir.exists()
    assert context.log_dir.exists()
    assert context.report_dir.exists()

    payload = json.loads(context.metadata_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == context.run_id
    assert metadata["config_path"] == str(CONFIG)
