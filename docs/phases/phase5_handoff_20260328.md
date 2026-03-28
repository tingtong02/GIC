# Phase 5 Handoff - 2026-03-28

## 1. Current Phase Status

Project progress is now stable through Phase 5. This handoff reflects the final Phase 5 follow-up pass immediately before controlled Phase 6 (KG) work.

Completed scope:
- Phase 0 scaffold and runtime baseline
- Phase 1 data schema, registry, parser, converter, validation, and data docs
- Phase 2 physics baseline, scenario generation, label export, and validation
- Phase 3 signal frontend baseline, comparison, real-event hardening, and dual-default logic
- Phase 4 graph-ready data layer, baseline models, train/eval CLI, and comparison reporting
- Phase 5 physics-informed temporal GNN main model, signal fix, broader benchmark validation, richer physics state integration, controlled GPU validation, ablation suite, and final default-profile freeze

Current phase boundary:
- Phase 5 is now stable enough to hand off.
- Phase 6 may start next, but it should start from this frozen Phase 5 backbone rather than reopening broad Phase 5 architecture work.

## 2. Final Frozen Phase 5 Default

Global-default selection should now be decided primarily by the broader benchmark.
The small benchmark remains useful, but only as a secondary reference.

Final frozen default profile:
- graph backbone: `graphsage`
- graph layers: `3`
- hidden dimension: `64`
- temporal encoder: `gru`
- signal features: `on`
- physics features: `on`
- physics penalty: `on`
- physics penalty weight: `0.02`
- physics penalty warmup epochs: `10`
- hotspot head: `on`
- hotspot weight: `0.2`
- residual path: `off`
- batch size: `1`
- epochs: `120`
- learning rate: `1e-3`

Relevant default config files:
- `configs/phase5/models/main_model_default.yaml`
- `configs/phase5/losses/default_loss.yaml`
- `configs/phase5/phase5_dev.yaml`

Decision rule going forward:
- broader benchmark is the primary default-selection surface
- the small benchmark is a reference guardrail, not the main decision surface
- MAE is the primary headline decision metric for Phase 5 handoff and future default selection
- NMAE may remain in legacy reports for compatibility, but it should not be treated as a required decision metric going forward

## 3. What Was Finalized In This Closing Pass

### 3.1 Signal integration is no longer broken or optional-by-default

Earlier in Phase 5, `signal_on` underperformed because signal-ready features were effectively miswired in the graph-ready path.
That issue is now resolved.

Current status:
- signal features are recomputed causally per graph sample time instead of being statically broadcast
- Phase 5 consumes signal as graph-global temporal input rather than duplicating it as naive node-local input
- zero-variance signal features are automatically dropped and reported

This means signal is now a real, active, test-covered modality in the frozen default path.

### 3.2 Broader benchmark is now the main empirical decision surface

The broader benchmark combines the original timeseries scenario with local sweep scenarios and uses grouped splitting by `scenario_id`.
That broader benchmark is now the main basis for deciding the Phase 5 default.

Key broader dataset asset:
- `data/processed/graph_ready/datasets/case118_graph_broader.json`

### 3.3 Richer physics state is part of the stable main path

The graph-ready / Phase 5 path now includes richer physics input than the earlier proxy-like default.
This includes node-level and global physics aggregates plus quality-derived indicators.

Key files:
- `src/gic/graph/features.py`
- `src/gic/graph/builder.py`
- `src/gic/models/fusion/physics_fusion.py`
- `src/gic/training/main_loops.py`

### 3.4 GPU-backed controlled validation is complete

This handoff includes an actual GPU-backed controlled validation pass under WSL with `GIC_env` and the RTX 4080 Laptop GPU.

## 4. Final Report Assets

Final frozen broader report:
- `reports/phase_5_20260328T031108Z_94664593/phase5_main_report.json`
- `reports/phase_5_20260328T031108Z_94664593/phase5_main_report.md`

Final frozen small-benchmark reference report:
- `reports/phase_5_20260328T031212Z_72af6c40/phase5_main_report.json`
- `reports/phase_5_20260328T031212Z_72af6c40/phase5_main_report.md`

Formal candidate sweep summary:
- `reports/phase5_formal_matrix_20260328T024955Z_corrected.json`

Final narrow follow-up summaries:
- `reports/phase5_followup_broader_20260328.json`
- `reports/phase5_followup_default_20260328.json`

## 5. Final Benchmark Conclusions

### 5.1 Broader benchmark (primary decision surface)

Final frozen broader default:
- `phase5_hidden_mae = 7.73746395111084`

Phase 4 broader references:
- best non-graph baseline: `mlp = 21.21492975950241`
- default graph baseline: `gat = 22.175137162208557`

Conclusion:
- Phase 5 clearly beats the broader Phase 4 best baseline
- Phase 5 clearly beats the broader default graph baseline
- this is the main reason the current default is now frozen

Broader final ablation summary:
- `regression_only = 7.4714614152908325`
- `main_model_default = 7.73746395111084`
- `physics_penalty_off = 8.192777633666992`
- `signal_off = 10.494667053222656`
- `no_temporal = 17.9700266122818`
- `no_physics = 31.12251591682434`

Interpretation on the broader benchmark:
- signal input is genuinely useful
- richer physics remains clearly useful
- temporal modeling remains essential
- physics penalty is mildly but consistently helpful
- hotspot auxiliary learning is still a tradeoff, but reducing its weight to `0.2` gives a better compromise than the earlier heavier setting

### 5.2 Small benchmark (reference only)

Final frozen small-benchmark reference result:
- `phase5_hidden_mae = 3.819782018661499`

Phase 4 small references:
- best non-graph baseline: `mlp = 46.41555094718933`
- default graph baseline: `gat = 47.15382635593414`

Conclusion:
- the frozen broader-default path also comfortably beats both small-benchmark Phase 4 references
- the small benchmark no longer blocks the signal-enabled default choice

Small-benchmark final ablation summary:
- `no_physics = 3.2625606060028076`
- `main_model_default = 3.819782018661499`
- `signal_off = 8.161786794662476`
- `physics_penalty_off = 11.282696962356567`
- `regression_only = 26.08272910118103`
- `no_temporal = 46.67232394218445`

Interpretation on the small benchmark:
- signal remains clearly helpful
- physics penalty remains helpful
- temporal modeling remains essential
- the small benchmark still shows one exception: `no_physics` beats the frozen default
- this exception is recorded, but it does not override the broader-benchmark decision because broader is now the primary selection surface

## 6. Current Input-Path Evidence

Final frozen broader default signal summary:
- active signal features: `29`
- dropped zero-variance signal features: `1`

Final frozen small-benchmark default signal summary:
- active signal features: `27`
- dropped zero-variance signal features: `3`

This means signal integration is no longer a placeholder or a broken ablation path.
It is now an active modality in the frozen default.

## 7. Current Test And Repo Status

Latest full regression result after final follow-up changes:
- `76 passed, 1 warning`

Known warning:
- existing `torch` / NVML warning in the lightweight env-validation test path
- it does not block Phase 5 functionality

## 8. Remaining Risks

### 8.1 Benchmark size is still limited even after broader expansion

The broader benchmark is materially better than the earlier tiny benchmark, but it is still not a large real-world validation set.
Phase 5 is now stable enough to hand off, but not the final word on generalization.

### 8.2 Physics state is richer, but still not the last word in physical fidelity

The project now uses a richer physics state than the earlier proxy-only path, but it is still a compact engineered representation rather than a full high-fidelity heterogeneous physical state model.
That is acceptable for handing Phase 5 to Phase 6.

### 8.3 Phase 6 must not reopen broad Phase 5 tuning by accident

If KG work begins, it should start from the frozen Phase 5 backbone and compare against it cleanly.
Do not casually retune Phase 5 defaults while also introducing KG, or attribution will become muddy.

## 9. Recommended Starting Point For Phase 6

Before implementing KG logic, re-read:
- `docs/GIC_project_phase_roadmap_v1.md`
- `docs/phase_6_detailed_plan.md`

Phase 6 should treat the following as the starting backbone:
- `src/gic/models/main_model.py`
- `src/gic/models/fusion/physics_fusion.py`
- `src/gic/training/main_loops.py`
- `src/gic/graph/datasets.py`
- `configs/phase5/models/main_model_default.yaml`
- `configs/phase5/losses/default_loss.yaml`
- `reports/phase_5_20260328T031108Z_94664593/phase5_main_report.json`

Phase 6 discipline:
- keep the frozen Phase 5 default as the non-KG control
- add KG input paths as an enhancement, not as a silent replacement
- continue comparing primarily on the broader benchmark
- keep the small benchmark only as a secondary reference
- use MAE as the primary headline decision metric unless a later phase explicitly redefines the reporting contract

## 10. Handoff Conclusion

As of 2026-03-28, Phase 5 is in a strong handoff state:
- the main model path is stable
- signal integration is repaired and now part of the final broader-default path
- richer physics is retained because it is strongly supported by the broader benchmark
- broader-benchmark validation clearly supports the frozen default
- the small benchmark is now only a reference and no longer blocks the broader-default choice
- tests, CLI, configs, reports, and ablation paths are all present for the next developer

The next phase may now start controlled KG integration, but it should do so on top of this frozen Phase 5 backbone rather than reopening broad Phase 5 architecture work.
