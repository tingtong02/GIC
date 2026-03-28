# Phase 6 Handoff - 2026-03-28

## 1. Current Phase Status

Project progress is now stable through Phase 6.
This handoff reflects the first complete KG pass after the frozen Phase 5 broader-default backbone was established.

Completed scope through Phase 6:
- Phase 0 scaffold and runtime baseline
- Phase 1 data schema, registry, parser, converter, validation, and data docs
- Phase 2 physics baseline, scenario generation, label export, and validation
- Phase 3 signal frontend baseline, comparison, real-event hardening, and dual-default logic
- Phase 4 graph-ready data layer, baseline models, train/eval CLI, and comparison reporting
- Phase 5 physics-informed temporal GNN main model, signal fix, broader benchmark validation, richer physics integration, controlled GPU validation, ablation suite, and frozen broader-default profile
- Phase 6 KG schema, entity-relation build pipeline, KG feature derivation, rule/query layer, model-level fusion, formal `no KG / with KG` comparison, and default KG enhancement recommendation

Current phase boundary:
- Phase 6 is now in handoff state.
- Later phases should treat the frozen Phase 5 backbone plus the Phase 6 KG default as explicit baselines rather than reopening broad Phase 5 or Phase 6 architecture work without clear attribution.

## 2. Frozen Control And Current Default KG Path

### 2.1 Frozen non-KG control

The non-KG control for all Phase 6 comparisons is the frozen broader-benchmark Phase 5 default documented in:
- `reports/phase_5_20260328T031108Z_94664593/phase5_main_report.json`

That control corresponds to the broader-default Phase 5 path described in:
- `docs/phases/phase5_handoff_20260328.md`

### 2.2 Current recommended KG default

Global-default selection for KG should continue to use the broader benchmark as the primary decision surface.

Current recommended Phase 6 default path:
- KG enhancement mode: `feature_only`
- relation enhancement: `off`
- rule/query layer: `on` for explanation and diagnostics
- main config entry: `configs/phase6/phase6_dev.yaml`
- preferred model variant: `configs/phase6/models/feature_only_full.yaml`
- primary benchmark dataset: `data/processed/graph_ready/datasets/case118_graph_broader.json`

Current interpretation:
- KG is now a real model enhancement layer rather than only an organizational layer
- the current measurable gain comes from feature-level KG augmentation
- the rule layer is useful for traceability and queries, but not yet for predictive gain on the current broader dataset

## 3. What Phase 6 Added

### 3.1 KG foundation assets

Phase 6 now provides:
- KG schema with stable entity and relation field contracts
- normalized entity ids and relation ids
- validation and manifest generation
- source provenance tracking
- exported entities, relations, schema, manifest, features, and rule payloads under `data/processed/kg/`

### 3.2 KG feature path

Phase 6 added explicit KG-derived features into the main model input bundle without silently modifying the Phase 5 baseline.

Current active KG feature types include:
- graph-global scenario type and scenario progress context
- graph-global time-from-start context
- node-level connectivity and equipment-neighborhood aggregates
- node-level line-length, resistance, azimuth, and transformer summary features

### 3.3 Rule and query path

Phase 6 added lightweight rules and query support for:
- assumptions
- quality flags
- signal-context availability
- per-sample queryable explanation payloads

This means KG now has both:
- a predictive enhancement path
- a traceability / explanation path

## 4. Final Report Assets

Formal broader-benchmark KG ablation report:
- `reports/phase_6_20260328T111606Z_70f7f7a9/phase6_kg_ablation_report.json`

Formal broader-benchmark KG report:
- `reports/phase_6_20260328T111725Z_1c65ed09/phase6_kg_report.json`
- `reports/phase_6_20260328T111725Z_1c65ed09/phase6_kg_report.md`

Key supporting documentation:
- `docs/models/kg_overview.md`
- `docs/data/kg_schema.md`
- `docs/decisions/0006_phase6_kg_design.md`

## 5. Final Benchmark Conclusions

### 5.1 Broader benchmark (primary decision surface)

Formal Phase 6 broader comparison:
- frozen Phase 5 / `no_kg`: hidden-node MAE `7.73746395111084`
- Phase 6 `feature_only`: hidden-node MAE `5.947530508041382`
- Phase 6 `kg_default`: hidden-node MAE `5.947530508041382`

Conclusion:
- Phase 6 KG helps the primary benchmark
- the broader benchmark requirement from the Phase 6 plan is satisfied
- Phase 6 now has a real model-level gain rather than only better organization or explanation

### 5.2 Why `feature_only` is the current default

`feature_only` and `kg_default` tie on the current broader benchmark.
However, the rule-derived model-feature branch currently contributes no active predictive features on this dataset because those rule features are zero-variance after train-split filtering.

Therefore the recommended default is:
- keep the leaner `feature_only` predictive path
- keep the rule layer available for explanation and query workflows
- do not require rule-derived model features in the default predictive configuration until they show measurable gain on the primary benchmark

## 6. Current KG Asset State

Current broader-dataset KG summary:
- entity count: `47`
- relation count: `169`
- graph sample count with KG features: `14`
- exported graph-global KG feature count: `19`
- exported node-level KG feature count: `12`

Current entity types include:
- `Grid`
- `Region`
- `Substation`
- `Bus`
- `Transformer`
- `TransmissionLine`
- `Sensor`
- `MagnetometerStation`
- `StormEvent`
- `Scenario`
- `Observation`
- `AssumptionRecord`

Current relation types include:
- `connected_to`
- `located_in`
- `belongs_to`
- `contains`
- `observes`
- `influenced_by`
- `has_sensor`
- `mapped_to`
- `generated_from`
- `associated_with_event`
- `derived_under_scenario`
- `constrained_by`

## 7. Current Test And Repo Status

Phase 6 targeted regression during the closing pass covered:
- KG schema / builder / rules / features
- main-model KG input path
- training loop KG path
- Phase 6 CLI report and ablation commands

Phase 6 targeted tests passed during this closing pass.
The broader GPU-backed report and ablation were also executed successfully outside the sandbox under `GIC_env`.

## 8. Current Benefit Boundary

### 8.1 Where KG clearly helps now

KG currently helps through:
- graph-global scenario and temporal context that is not cleanly represented in the frozen non-KG path
- node-level topology and equipment-neighborhood context
- explicit assumption and provenance organization
- queryable explanation support for difficult samples

### 8.2 Where KG is currently limited

Current limits:
- the broader benchmark is still not a large real-world validation set
- rule-derived model features do not add predictive gain on the current broader dataset
- relation-aware graph enhancement has not been promoted beyond an extension path yet

### 8.3 Attribution guidance going forward

If a later phase changes KG behavior, it should continue to compare against:
- frozen Phase 5 broader default as the non-KG control
- Phase 6 `feature_only` as the current default KG-enhanced control

Do not silently merge new KG logic into the backbone and lose attribution.

## 9. Recommended Starting Point For The Next Phase

Before continuing beyond Phase 6, re-read:
- `docs/GIC_project_phase_roadmap_v1.md`
- `docs/phase_7_detailed_plan.md` if moving to real-event validation
- `docs/models/kg_overview.md`
- this handoff file

Recommended baseline set for future controlled comparisons:
- frozen Phase 5 non-KG broader default
- Phase 6 `feature_only` broader default

Recommended discipline:
- keep broader benchmark MAE as the primary decision metric
- keep the small benchmark only as a secondary reference unless a later phase explicitly changes that rule
- keep KG rule/query support available even when rule-derived predictive features remain off by default

## 10. Handoff Conclusion

As of 2026-03-28, Phase 6 is in a strong handoff state:
- KG schema, exports, validation, and manifests are present
- KG feature derivation is integrated into the main model input path with explicit switches
- `no KG / with KG` model-level comparison is implemented and reproducible
- KG delivers a measurable broader-benchmark gain over the frozen non-KG Phase 5 control
- the current recommended default KG enhancement path is `feature_only`
- rule/query support is useful and test-covered, but rule-derived model features are not yet part of the default predictive path

This means the project can now move forward with a clear Phase 6 outcome:
KG is no longer only an organizational layer; it is a controlled and beneficial model enhancement on the primary benchmark, with a well-defined current boundary.
