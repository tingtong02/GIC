from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gic.graph.schema import GraphManifest


@dataclass(slots=True)
class GraphDataset:
    dataset_name: str
    manifest_path: str
    graph_paths: list[str]
    split_assignments: dict[str, list[str]]
    metadata: dict[str, Any]

    @classmethod
    def from_path(cls, dataset_path: str | Path) -> 'GraphDataset':
        payload = json.loads(Path(dataset_path).read_text(encoding='utf-8'))
        return cls(
            dataset_name=str(payload['dataset_name']),
            manifest_path=str(payload['manifest_path']),
            graph_paths=[str(item) for item in payload.get('graph_paths', [])],
            split_assignments={str(key): [str(item) for item in value] for key, value in payload.get('split_assignments', {}).items()},
            metadata=dict(payload.get('metadata', {})),
        )

    def __len__(self) -> int:
        return len(self.graph_paths)

    def graph_ids(self) -> list[str]:
        return [Path(path).stem for path in self.graph_paths]



def build_split_assignments(graph_ids: list[str], split_config: dict[str, float]) -> dict[str, list[str]]:
    ordered = list(graph_ids)
    total = len(ordered)
    if total == 0:
        return {'train': [], 'val': [], 'test': []}
    train_ratio = float(split_config.get('train', 0.6))
    val_ratio = float(split_config.get('val', 0.2))
    train_count = max(1, int(total * train_ratio))
    val_count = max(1, int(total * val_ratio)) if total >= 3 else max(0, total - train_count - 1)
    if train_count + val_count >= total:
        val_count = max(0, total - train_count - 1)
    test_count = max(0, total - train_count - val_count)
    if test_count == 0 and total >= 3:
        test_count = 1
        if train_count > 1:
            train_count -= 1
        elif val_count > 0:
            val_count -= 1
    return {
        'train': ordered[:train_count],
        'val': ordered[train_count:train_count + val_count],
        'test': ordered[train_count + val_count:train_count + val_count + test_count],
    }



def load_graph_manifest(path: str | Path) -> GraphManifest:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    return GraphManifest(**payload)
