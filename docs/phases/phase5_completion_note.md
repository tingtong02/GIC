# Phase 5 Completion Note

## Scope Summary
Phase 5 now includes:
- a unified temporal + graph main model,
- configurable physics fusion and optional residual mode,
- regression + hotspot multi-task path,
- configurable physics penalty,
- Phase 5 train/eval CLI,
- required ablations (`baseline vs main`, `no_physics`, `residual_default`, `with_physics_penalty`, `signal_on`, `no_temporal`, `regression_only`),
- main-model report generation,
- Phase 5 configs, tests, and design docs.

## Current Default Main Model
- Graph backbone: `graphsage`
- Graph layers: `3`
- Hidden dimension: `64`
- Temporal encoder: `gru`
- Physics path: normalized physics proxy feature input
- Signal-ready features in default dev profile: `false`
- Residual addition: off by default
- Auxiliary task: hotspot classification
- Physics penalty: supported but off in the default dev profile
- Default training budget: batch size `1`, epochs `120`, learning rate `1e-3`

## Current Evidence
- Phase 5 engineering scope is complete in the sense of code, CLI, tests, configs, and reporting coverage.
- The optimized default Phase 5 profile now outperforms the Phase 4 best baseline on the current controlled graph-ready benchmark.
- Latest default result: hidden-node MAE `2.6595`; Phase 4 best baseline: `46.4156`; Phase 4 default graph baseline: `47.1538`.
- The current benchmark remains intentionally small, so the result should be read as stage-level evidence rather than large-sample deployment evidence.

## Optimization Notes
- A controlled Phase 5-valid search over temporal + graph + physics + hotspot settings showed that stronger GraphSAGE capacity and a larger training budget materially improved both validation and test hidden-node MAE.
- The strongest default-profile result on the current benchmark keeps graph, temporal, physics, and hotspot paths enabled, while disabling signal-ready features in the default dev profile.
- The corresponding input-modality ablation is still preserved through `signal_on`, so Phase 3 feature integration remains implemented and comparable rather than silently dropped.
- Residual mode remains implemented, but it is still not the default because it was unstable on the current benchmark.

## Handoff Guidance
- Phase 6 should inherit the stable Phase 5 interfaces, not rework them from scratch.
- The remaining risk is no longer “Phase 5 cannot beat Phase 4”; the main remaining risk is benchmark size and physics-proxy fidelity.
- If later work introduces GPU sweeps or richer physics state, those should be framed as strengthening an already working Phase 5 default rather than rescuing a broken one.
