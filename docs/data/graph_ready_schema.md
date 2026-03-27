# Graph Ready Schema

Core exported objects:
- `GraphSample`: one graph snapshot with `graph_id`, `sample_id`, `scenario_id`, `time_index`, `node_records`, `edge_records`, `feature_bundle`, `label_bundle`, `mask_bundle`, and `metadata`
- `GraphFeatureBundle`: `node_feature_names`, `node_features`, optional `global_feature_names`, optional `global_features`, and `quality_flags`
- `GraphLabelBundle`: `target_level`, `objective`, `target_names`, `node_targets`, `transformer_targets`, and `metadata`
- `MaskBundle`: `sparsity_rate`, `observed_nodes`, `target_nodes`, `observed_mask`, `target_mask`, and `metadata`
- `GraphManifest`: dataset-level export summary with graph paths, split assignments, sparsity rate, task payload, and path metadata

Current Phase 4 design choices:
- Bus is the primary node type
- Electrical connectivity edges are exported in both directions
- Sparse observation is recorded explicitly in `MaskBundle`
- Graph-ready exports are written to `data/processed/graph_ready/` and are reusable across later baselines
- Each exported dataset now writes samples to `data/processed/graph_ready/samples/<dataset_name>/` so different sparsity and feature variants do not overwrite each other during ablation
