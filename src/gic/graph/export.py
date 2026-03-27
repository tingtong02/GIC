from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gic.graph.schema import GraphManifest, GraphSample, graph_to_dict
from gic.utils.paths import ensure_directory


def _export_root(project_root: Path, graph_config: dict[str, Any]) -> Path:
    return ensure_directory(project_root / graph_config['output_root'])


def export_graph_samples(
    *,
    project_root: Path,
    graph_config: dict[str, Any],
    dataset_name: str,
    source_case_id: str,
    scenario_id: str,
    task_payload: dict[str, Any],
    graph_samples: list[GraphSample],
    split_assignments: dict[str, list[str]],
) -> tuple[GraphManifest, list[str]]:
    root = _export_root(project_root, graph_config)
    samples_root = ensure_directory(root / 'samples')
    manifests_root = ensure_directory(root / 'manifests')
    graph_paths: list[str] = []
    for sample in graph_samples:
        destination = samples_root / f'{sample.graph_id}.json'
        destination.write_text(json.dumps(graph_to_dict(sample), indent=2, sort_keys=True) + '\n', encoding='utf-8')
        graph_paths.append(str(destination))
    manifest_path = manifests_root / f'{dataset_name}.manifest.json'
    manifest = GraphManifest(
        dataset_name=dataset_name,
        source_case_id=source_case_id,
        scenario_id=scenario_id,
        graph_count=len(graph_samples),
        node_count=len(graph_samples[0].node_records) if graph_samples else 0,
        edge_count=len(graph_samples[0].edge_records) if graph_samples else 0,
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        graph_paths=graph_paths,
        split_assignments=split_assignments,
        sparsity_rate=float(graph_config.get('sparsity_rate', 0.0)),
        task=task_payload,
        notes='Phase 4 graph-ready export from Phase 2 physics labels and optional Phase 3 signal features.',
        paths={
            'manifest': str(manifest_path),
            'samples_root': str(samples_root),
        },
    )
    manifest_path.write_text(json.dumps(graph_to_dict(manifest), indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return manifest, graph_paths


def export_graph_dataset(
    *,
    project_root: Path,
    graph_config: dict[str, Any],
    manifest: GraphManifest,
) -> str:
    root = _export_root(project_root, graph_config)
    datasets_root = ensure_directory(root / 'datasets')
    destination = datasets_root / f'{manifest.dataset_name}.json'
    payload = {
        'dataset_name': manifest.dataset_name,
        'manifest_path': manifest.paths.get('manifest', ''),
        'graph_paths': manifest.graph_paths,
        'split_assignments': manifest.split_assignments,
        'metadata': {
            'source_case_id': manifest.source_case_id,
            'scenario_id': manifest.scenario_id,
            'sparsity_rate': manifest.sparsity_rate,
            'task': manifest.task,
            'generated_at_utc': manifest.generated_at_utc,
        },
    }
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return str(destination)
