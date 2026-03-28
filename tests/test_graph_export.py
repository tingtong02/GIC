from __future__ import annotations

from pathlib import Path

from gic.config import load_config
from gic.graph import (
    GraphDataset,
    build_graph_samples_from_config,
    build_split_assignments,
    export_graph_dataset,
    export_graph_samples,
    load_graph_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
PHASE4_CONFIG = ROOT / 'configs/phase4/phase4_broader_benchmark.yaml'


def test_graph_export_writes_manifest_and_dataset(tmp_path: Path) -> None:
    config = load_config(PHASE4_CONFIG)
    _, build_context, samples = build_graph_samples_from_config(ROOT, config)
    scenario_group_assignments = {sample.graph_id: str(sample.scenario_id) for sample in samples}
    split_assignments = build_split_assignments(
        [item.graph_id for item in samples],
        config['graph']['split'],
        group_assignments=scenario_group_assignments,
    )
    manifest, graph_paths = export_graph_samples(
        project_root=tmp_path,
        graph_config=config['graph'],
        dataset_name=build_context['dataset_name'],
        source_case_id=build_context['source_case_id'],
        scenario_id=build_context['scenario_id'],
        task_payload=build_context['task'],
        graph_samples=samples,
        split_assignments=split_assignments,
    )
    dataset_path = export_graph_dataset(project_root=tmp_path, graph_config=config['graph'], manifest=manifest)
    loaded_manifest = load_graph_manifest(manifest.paths['manifest'])
    dataset = GraphDataset.from_path(dataset_path)
    assert len(graph_paths) == len(samples)
    assert loaded_manifest.graph_count == len(samples)
    assert len(dataset) == len(samples)
    assert set(dataset.split_assignments) == {'train', 'val', 'test'}
    graph_to_scenario = {sample.graph_id: str(sample.scenario_id) for sample in samples}
    scenario_to_splits: dict[str, set[str]] = {}
    for split_name, graph_ids in dataset.split_assignments.items():
        for graph_id in graph_ids:
            scenario_to_splits.setdefault(graph_to_scenario[graph_id], set()).add(split_name)
    assert all(len(splits) == 1 for splits in scenario_to_splits.values())
