# Real Event Validation Overview

## Goal

Phase 7 validates the project under real geomagnetic storm inputs without overstating what the available evidence can support.

## Event Set

- Main validation event: INTERMAGNET 2020-09-01 smoke window
- Generalization event: INTERMAGNET 2020-10-01 smoke window
- Boundary event: INTERMAGNET 2020-11-01 smoke window
- Stations: BOU, FRD, OTT

## Model Set

- Phase 4 best graph baseline
- Phase 5 frozen default main model
- Phase 6 frozen `feature_only` KG enhancement

## Evidence Policy

- No local geomagnetic station series is treated as full-network GIC truth.
- Direct numeric MAE against physics-generated labels is reported only as proxy consistency, not as real-world accuracy.
- Real-world conclusions are built mainly from trend, peak timing, ranking, and grouped evidence reports.

## Output Structure

Phase 7 should export:

- frozen event manifests
- evidence bundles
- event-level evaluation results
- grouped generalization / robustness reports
- failure cases
- trustworthiness summary

## Primary Risks

- no direct transformer-neutral GIC labels
- mapping from North America station windows to the case118 proxy grid remains approximate
- signal frontend availability varies by event unless exported on demand
