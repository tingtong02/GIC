# Phase 6 Completion Note

Phase 6 is complete at the minimum required acceptance level and beyond.

What is complete:
- KG schema, entity export, relation export, manifest, validation, and source provenance
- KG feature derivation for graph-global and node-level features
- lightweight rule and query support
- Phase 6 CLI for schema build, graph build, feature export, ablation, report build, and sample query
- explicit `no KG / with KG` model-level comparison against the frozen Phase 5 broader-benchmark baseline
- a default KG enhancement recommendation with reportable value boundary

Primary result on the broader benchmark:
- frozen Phase 5 / `no_kg`: hidden-node MAE `7.73746395111084`
- Phase 6 recommended variant / `feature_only`: hidden-node MAE `5.947530508041382`

Current default Phase 6 recommendation:
- keep the frozen Phase 5 backbone
- enable KG feature-level enhancement
- keep relation enhancement off by default
- keep rule/query support enabled for explanation and diagnostics
- prefer `configs/phase6/models/feature_only_full.yaml`

Current limitation:
- rule-derived model features do not improve the broader benchmark yet because they are zero-variance on the current broader dataset
- the broader benchmark is still relatively small, so Phase 6 is complete but not the final word on generalization
