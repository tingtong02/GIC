# Phase 5 Main Model Overview

## Main Tasks
- Primary task: node-level GIC regression on the Phase 4 graph-ready dataset.
- Auxiliary task: hotspot classification derived from the target-time absolute GIC quantile.

## Architecture
- `InputEncoder`: aligns graph-ready node features for every step in the sliding window.
- `TemporalEncoder`: default `gru`, with `none` as the no-temporal ablation.
- `GraphBackbone`: default `graphsage`, sharing the same graph-ready adjacency semantics used in Phase 4.
- `PhysicsFusion`: injects the Phase 2-derived physics proxy feature; residual mode is implemented but is not the default dev profile.
- `TaskHeads`: regression head is always on; hotspot head is enabled by default; risk and uncertainty heads remain optional interfaces.
- `LossComposer`: combines Huber regression, hotspot BCE, and optional physics penalty.

## Inputs And Outputs
- Inputs: graph adjacency, sliding-window node features, observed mask, physics baseline proxy, and aligned metadata.
- Outputs: regression prediction, hotspot logits, optional risk score, optional uncertainty, plus metadata needed for reporting.

## Relation To Phase 4
- Uses the same graph-ready dataset, split assignments, node targets, and hidden-node MAE reporting path.
- Keeps Phase 4 comparability by reading the Phase 4 baseline report directly for main-vs-baseline comparison.

## Default Configuration
- Graph backbone: `graphsage`
- Temporal encoder: `gru`
- Physics fusion: normalized physics feature input
- Residual enabled: `false`
- Enabled heads: regression + hotspot
- Default loss: Huber + hotspot BCE; physics penalty remains available but is off in the default dev profile

## Known Limitations
- Current temporal dataset is intentionally small, so rankings and gains should be read as controlled baseline evidence rather than large-sample claims.
- The physics baseline used in Phase 5 is the graph-ready physics proxy exported during Phase 4, not a richer heterogeneous physics state.
- Risk-score and uncertainty heads are exposed as interfaces but are not part of the default experiment path.
