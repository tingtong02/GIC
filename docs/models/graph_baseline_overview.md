# Graph Baseline Overview

Phase 4 establishes a bus-node graph-ready baseline before any physics-informed or KG-enhanced model work.

Current Phase 4 graph task:
- Main node type: `bus`
- Main task: node-level GIC regression from sparse observations
- Edge family: electrical connectivity from lines and transformers
- Optional auxiliary features: Phase 3 signal-ready summaries and Phase 2-derived physics adjacency features

Why this phase does not include later-stage methods:
- No physics-informed losses or message passing in Phase 4
- No KG schema or relation-aware graph learning in Phase 4
- No end-to-end signal frontend + graph joint training in Phase 4

Current baseline scope in this initial implementation pass:
- Graph-ready schema and export layer are implemented first
- Dataset reading and split metadata are implemented first
- Non-graph and graph model baselines remain the next Phase 4 step, with `mlp` and `gcn` as the default planned starting baselines

Known limits:
- Current graph is single-node-type only
- Signal features are broadcast graph-level summaries rather than node-specific sensor features
- Training and ablation loops are intentionally not implemented in this first graph-ready pass
