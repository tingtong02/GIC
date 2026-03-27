from __future__ import annotations

import hashlib

from gic.graph.schema import MaskBundle



def build_observation_mask(node_ids: list[str], sparsity_rate: float, seed: int, graph_id: str) -> MaskBundle:
    total_nodes = len(node_ids)
    hidden_count = min(total_nodes - 1, max(0, int(round(total_nodes * sparsity_rate)))) if total_nodes > 1 else 0
    observed_count = max(1, total_nodes - hidden_count) if total_nodes else 0
    ranked = sorted(
        node_ids,
        key=lambda node_id: hashlib.sha256(f'{seed}:{graph_id}:{node_id}'.encode('utf-8')).hexdigest(),
    )
    observed_nodes = sorted(ranked[:observed_count])
    target_nodes = sorted(node_ids)
    observed_mask = {node_id: node_id in observed_nodes for node_id in node_ids}
    target_mask = {node_id: True for node_id in node_ids}
    return MaskBundle(
        sparsity_rate=float(sparsity_rate),
        observed_nodes=observed_nodes,
        target_nodes=target_nodes,
        observed_mask=observed_mask,
        target_mask=target_mask,
        metadata={
            'seed': int(seed),
            'observed_fraction': (len(observed_nodes) / total_nodes) if total_nodes else 0.0,
            'hidden_fraction': (hidden_count / total_nodes) if total_nodes else 0.0,
        },
    )
