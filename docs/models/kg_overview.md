# KG Overview

## Role

Phase 6 KG is a controlled enhancement layer for GIC reconstruction. It organizes heterogeneous assets, exports traceable KG-derived features, and supports lightweight rule and query workflows without replacing the frozen Phase 5 backbone.

## Default Path

The current recommended Phase 6 default path is `feature_only` on top of the frozen broader-benchmark Phase 5 backbone.

Current default role mix:
- role A: heterogeneous data organization
- role B: model enhancement through derived features
- role C: lightweight assumption and quality rules for traceability and diagnostics
- role D: query and explanation support

Current default modeling choice:
- use KG-derived global and node features in the main model input bundle
- keep relation enhancement off by default
- keep the rule layer enabled for reporting and querying
- do not require rule-derived model features unless they provide measurable gain on the primary benchmark

## Why This Is The Default

The broader benchmark is the primary decision surface for Phase 6.

Formal broader-benchmark comparison on 2026-03-28:
- frozen Phase 5 / no KG hidden-node MAE: `7.73746395111084`
- Phase 6 `feature_only` hidden-node MAE: `5.947530508041382`
- Phase 6 `kg_default` hidden-node MAE: `5.947530508041382`

Interpretation:
- KG now provides a measurable main-task gain on the primary benchmark
- the gain currently comes from feature-level KG enhancement rather than rule-derived model features
- `feature_only` is preferred over `kg_default` because it reaches the same result with the leaner active path on the current dataset

## What KG Adds

- explicit entity and relation organization across graph-ready, physics-ready, and signal-ready assets
- stable KG-derived graph-global and node-level features with provenance
- explicit assumption and quality findings per sample
- queryable evidence for why a sample carries certain contextual risk or missingness flags
- a clean `no KG / with KG` comparison path against the frozen Phase 5 backbone

## What KG Does Not Add Yet

- a new prediction backbone
- a graph database platform
- complex inference or reasoning chains
- a silent replacement of Phase 5 features
- a demonstrated metric gain from rule-derived model features on the current broader dataset

## Current Benefit Boundary

KG is currently most useful as:
- topology-aware node context
- scenario/time-context augmentation
- assumption and quality traceability
- explanation and query support for difficult samples

KG is currently limited by:
- a still-small broader benchmark
- rule-derived features that are zero-variance on the current broader dataset and therefore not helpful to the predictive path yet
- the fact that relation-aware graph enhancement remains an extension path rather than the default Phase 6 route

## Default Applicability

Current recommended default applies to:
- data version: `data/processed/graph_ready/datasets/case118_graph_broader.json`
- frozen Phase 5 control: `reports/phase_5_20260328T031108Z_94664593/phase5_main_report.json`
- Phase 6 config entry: `configs/phase6/phase6_dev.yaml`
- preferred model variant: `configs/phase6/models/feature_only_full.yaml`
