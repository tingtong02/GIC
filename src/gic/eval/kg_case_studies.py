from __future__ import annotations

from typing import Any


def select_kg_query_examples(sample_index: dict[str, dict[str, Any]], *, top_k: int = 3) -> list[str]:
    ranked = sorted(
        sample_index.values(),
        key=lambda item: (len(item.get('quality_flags', [])) + len(item.get('assumptions', [])), str(item.get('graph_id', ''))),
        reverse=True,
    )
    return [str(item['graph_id']) for item in ranked[:top_k]]
