from __future__ import annotations

from pathlib import Path
from typing import Any

from gic.pipelines.final_pipeline import run_final_pipeline


def run_final_evaluation(*, project_root: Path, config: dict[str, Any], with_kg: bool | None = None, check_only: bool = False, registry: Any = None, report_destination_root: Path | None = None) -> dict[str, Any]:
    return run_final_pipeline(
        project_root=project_root,
        config=config,
        with_kg=with_kg,
        check_only=check_only,
        registry=registry,
        report_destination_root=report_destination_root,
    )


def run_final_real_evaluation(*, project_root: Path, config: dict[str, Any], with_kg: bool | None = None, check_only: bool = False, registry: Any = None, report_destination_root: Path | None = None) -> dict[str, Any]:
    return run_final_pipeline(
        project_root=project_root,
        config=config,
        with_kg=with_kg,
        check_only=check_only,
        refresh_real_eval=True,
        registry=registry,
        report_destination_root=report_destination_root,
    )
