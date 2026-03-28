from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gic.graph.datasets import GraphDataset, GraphSample
from gic.utils.paths import resolve_path


@dataclass(slots=True)
class KGRawSources:
    dataset_path: Path
    dataset: GraphDataset
    dataset_payload: dict[str, Any]
    graph_manifest: dict[str, Any]
    graph_samples: list[GraphSample]
    physics_case_path: Path | None
    physics_case: dict[str, Any]
    grid_case_path: Path | None
    grid_case: dict[str, Any]
    signal_manifests: dict[str, dict[str, Any]]


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def _grid_case_path(project_root: Path, source_case_id: str | None) -> Path | None:
    if not source_case_id:
        return None
    candidate = project_root / 'data' / 'interim' / 'grid_cases' / f'{source_case_id}.json'
    return candidate.resolve() if candidate.exists() else None


def load_kg_sources(dataset_path: str | Path, *, project_root: Path) -> KGRawSources:
    resolved_dataset_path = resolve_path(project_root, dataset_path)
    dataset_payload = json.loads(resolved_dataset_path.read_text(encoding='utf-8'))
    dataset = GraphDataset.from_path(resolved_dataset_path)
    graph_manifest = _read_json(Path(dataset.manifest_path)) if dataset.manifest_path else {}
    graph_samples = dataset.load_all_samples()
    first_sample = graph_samples[0] if graph_samples else None
    physics_case_path = None
    if first_sample is not None and first_sample.metadata.get('physics_case_path'):
        physics_case_path = resolve_path(project_root, str(first_sample.metadata['physics_case_path']))
    physics_case = _read_json(physics_case_path)
    source_case_id = str(first_sample.metadata.get('source_case_id')) if first_sample is not None and first_sample.metadata.get('source_case_id') else None
    grid_case_path = _grid_case_path(project_root, source_case_id)
    grid_case = _read_json(grid_case_path)
    signal_manifests: dict[str, dict[str, Any]] = {}
    for sample in graph_samples:
        manifest_path = sample.metadata.get('signal_manifest_path')
        if not manifest_path:
            continue
        resolved_manifest_path = str(resolve_path(project_root, str(manifest_path)))
        if resolved_manifest_path not in signal_manifests:
            signal_manifests[resolved_manifest_path] = _read_json(Path(resolved_manifest_path))
    return KGRawSources(
        dataset_path=resolved_dataset_path,
        dataset=dataset,
        dataset_payload=dataset_payload,
        graph_manifest=graph_manifest,
        graph_samples=graph_samples,
        physics_case_path=physics_case_path,
        physics_case=physics_case,
        grid_case_path=grid_case_path,
        grid_case=grid_case,
        signal_manifests=signal_manifests,
    )
