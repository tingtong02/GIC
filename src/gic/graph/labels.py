from __future__ import annotations

from typing import Any

from gic.graph.schema import GraphLabelBundle, ReconstructionTaskConfig



def build_label_bundle(solution: dict[str, Any], task: ReconstructionTaskConfig) -> GraphLabelBundle:
    node_targets = {
        str(item['bus_id']): float(item['solved_quantity'])
        for item in solution.get('bus_quantities', [])
    }
    transformer_targets = {
        str(item['transformer_id']): float(item['gic_value'])
        for item in solution.get('transformer_gic', [])
    }
    return GraphLabelBundle(
        target_level=task.target_level,
        objective=task.objective,
        target_names=['gic_value'],
        node_targets=node_targets,
        transformer_targets=transformer_targets,
        metadata={
            'solution_id': solution.get('solution_id'),
            'time': solution.get('time'),
        },
    )
