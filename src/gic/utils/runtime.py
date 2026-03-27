from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from gic.config.loader import write_config_snapshot
from gic.utils.metadata import build_metadata
from gic.utils.paths import ensure_directory, resolve_path, resolve_project_root


@dataclass(slots=True)
class RunContext:
    run_id: str
    artifact_dir: Path
    log_dir: Path
    report_dir: Path
    config_snapshot_path: Path
    metadata_path: Path
    summary_path: Path
    log_file: Path


def generate_run_id(stage: str) -> str:
    slug = stage.lower().replace(" ", "_")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    token = uuid4().hex[:8]
    return f"{slug}_{stamp}_{token}"


def prepare_run(config: dict, project_root: str | Path | None = None) -> RunContext:
    root = resolve_project_root(project_root)
    paths_cfg = config["paths"]
    run_id = generate_run_id(config["project"]["stage"])

    artifact_dir = ensure_directory(resolve_path(root, paths_cfg["artifacts_root"]) / run_id)
    log_dir = ensure_directory(resolve_path(root, paths_cfg["logs_root"]) / run_id)
    report_dir = ensure_directory(resolve_path(root, paths_cfg["reports_root"]) / run_id)

    return RunContext(
        run_id=run_id,
        artifact_dir=artifact_dir,
        log_dir=log_dir,
        report_dir=report_dir,
        config_snapshot_path=artifact_dir / paths_cfg["config_snapshot_name"],
        metadata_path=artifact_dir / paths_cfg["metadata_name"],
        summary_path=report_dir / paths_cfg["summary_name"],
        log_file=log_dir / paths_cfg["log_filename"],
    )


def initialize_run(
    *,
    config: dict,
    config_path: str,
    command: str,
    project_root: str | Path | None = None,
) -> tuple[RunContext, dict]:
    context = prepare_run(config, project_root=project_root)
    root = resolve_project_root(project_root)
    write_config_snapshot(config, context.config_snapshot_path)
    metadata = build_metadata(
        run_id=context.run_id,
        config_path=config_path,
        command=command,
        project_root=root,
        artifact_dir=context.artifact_dir,
        log_file=context.log_file,
        summary_path=context.summary_path,
    )
    context.metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return context, metadata


def write_summary(context: RunContext, summary: dict) -> Path:
    context.summary_path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return context.summary_path
