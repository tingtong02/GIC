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

Current baseline scope in this implementation pass:
- Graph-ready schema, export layer, dataset reading, and split metadata are implemented
- `mlp` non-graph baseline is implemented on top of exported graph-ready data
- `gcn`, `graphsage`, and `gat` graph baselines are implemented on the same dataset interface and training loop
- `train-baseline`, `eval-baseline`, and `graph-build-report` all consume the same exported graph-ready datasets
- Phase 4 reporting now includes baseline ranking, reconstruction export, sparsity ablation, and signal/physics feature toggles

Current default Phase 4 recommendation:
- Default graph baseline: `gat`
- Best overall model on the default Phase 4 dataset is currently `mlp`
- Current graph baseline does not yet outperform the non-graph baseline on hidden-node MAE, so Phase 4 should be treated as a completed baseline-building stage rather than evidence that graph structure is already winning on this dataset

Known limits:
- Current graph is single-node-type only
- Signal features are broadcast graph-level summaries rather than node-specific sensor features
- The current Phase 4 dataset is very small, so ranking stability is limited
- Graph gains are not yet established on the default benchmark, which is now an explicit Phase 5 motivation rather than something hidden inside Phase 4 reporting
