from __future__ import annotations

from gic.graph.schema import GraphManifest, GraphSample



def validate_graph_sample(sample: GraphSample) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    node_ids = [item.node_id for item in sample.node_records]
    edge_node_ids = {item.source_node for item in sample.edge_records} | {item.target_node for item in sample.edge_records}
    if not node_ids:
        errors.append('GraphSample has no nodes')
    if not sample.edge_records:
        warnings.append('GraphSample has no edges')
    if not set(edge_node_ids).issubset(set(node_ids)):
        errors.append('GraphSample contains edges with unknown node references')
    for node_id in node_ids:
        values = sample.feature_bundle.node_features.get(node_id)
        if values is None:
            errors.append(f'Missing node features for {node_id}')
            continue
        if len(values) != len(sample.feature_bundle.node_feature_names):
            errors.append(f'Feature length mismatch for {node_id}')
        if node_id not in sample.mask_bundle.observed_mask:
            errors.append(f'Missing observed mask for {node_id}')
        if node_id not in sample.label_bundle.node_targets:
            warnings.append(f'Missing node target for {node_id}')
    return {
        'asset_id': sample.graph_id,
        'asset_type': 'graph_sample',
        'ok': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'stats': {
            'node_count': len(sample.node_records),
            'edge_count': len(sample.edge_records),
            'sparsity_rate': sample.mask_bundle.sparsity_rate,
        },
    }



def validate_graph_manifest(manifest: GraphManifest) -> dict[str, object]:
    errors: list[str] = []
    if manifest.graph_count <= 0:
        errors.append('GraphManifest graph_count must be positive')
    if manifest.node_count <= 0:
        errors.append('GraphManifest node_count must be positive')
    return {
        'asset_id': manifest.dataset_name,
        'asset_type': 'graph_manifest',
        'ok': len(errors) == 0,
        'errors': errors,
        'warnings': [],
        'stats': {
            'graph_count': manifest.graph_count,
            'node_count': manifest.node_count,
            'edge_count': manifest.edge_count,
        },
    }
