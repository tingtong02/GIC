from __future__ import annotations

import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _run_git(args: list[str], project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


def build_metadata(
    *,
    run_id: str,
    config_path: str,
    command: str,
    project_root: Path,
    artifact_dir: Path,
    log_file: Path,
    summary_path: Path,
) -> dict[str, Any]:
    dirty_output = _run_git(["status", "--short"], project_root)
    return {
        "run_id": run_id,
        "command": command,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "config_path": config_path,
        "project_root": str(project_root),
        "cwd": str(Path.cwd().resolve()),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV", ""),
        "git_commit": _run_git(["rev-parse", "HEAD"], project_root),
        "git_dirty": bool(dirty_output),
        "paths": {
            "artifact_dir": str(artifact_dir),
            "log_file": str(log_file),
            "summary_path": str(summary_path),
        },
    }
