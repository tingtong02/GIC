from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from gic.physics.postprocess import solution_to_dict, summarize_solution
from gic.physics.schema import GICSolution, LabelManifest, ScenarioConfig, physics_to_dict
from gic.utils.paths import ensure_directory


def export_label_bundle(
    *,
    project_root: Path,
    outputs_config: dict,
    scenario: ScenarioConfig,
    solutions: list[GICSolution],
) -> dict[str, str]:
    physics_ready_root = ensure_directory(project_root / outputs_config["physics_ready_root"])
    datasets_root = ensure_directory(project_root / outputs_config["datasets_root"])
    manifests_root = ensure_directory(project_root / outputs_config["manifests_root"])

    solution_path = physics_ready_root / f"{scenario.scenario_id}_solutions.json"
    dataset_path = datasets_root / f"{scenario.scenario_id}_dataset.json"
    manifest_path = manifests_root / f"{scenario.scenario_id}_manifest.json"

    solution_path.write_text(
        json.dumps([solution_to_dict(item) for item in solutions], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    dataset_path.write_text(
        json.dumps([summarize_solution(item) for item in solutions], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    manifest = LabelManifest(
        dataset_name=scenario.scenario_id,
        sample_count=len(solutions),
        time_length=len(solutions),
        case_source=scenario.case_dataset,
        scenario_type=scenario.scenario_type,
        solver_version="dc_baseline_v1",
        schema_version="1.0",
        assumptions=list(scenario.assumptions),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        paths={
            "solutions": str(solution_path),
            "dataset": str(dataset_path),
            "manifest": str(manifest_path),
        },
    )
    manifest_path.write_text(json.dumps(physics_to_dict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"solutions": str(solution_path), "dataset": str(dataset_path), "manifest": str(manifest_path)}
