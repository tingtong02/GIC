# Phase 7 Completion Note

## Scope

Phase 7 completed the real-event validation layer for GIC with frozen model families from Phase 4, Phase 5, and Phase 6. The implementation stays conservative: it treats local geomagnetic observations as evidence-bearing inputs rather than full-network truth.

## Delivered Assets

- Real-event event-set configs and manifests under `configs/phase7/` and `data/processed/real_event/`
- Evidence-level schema and documentation
- Real-event evaluation, generalization, robustness, case-study, and reporting modules in `src/gic/eval/`
- Phase 7 CLI commands:
  - `real-build-event-set`
  - `real-run-eval`
  - `real-run-generalization`
  - `real-run-robustness`
  - `real-build-case-studies`
  - `real-build-report`
- Phase 7 reports under `reports/phase_7_*`

## Final Run Snapshot

Primary report:
- `reports/phase_7_20260329T075558Z_298a760a/phase7_real_event_report.json`
- `reports/phase_7_20260329T075558Z_298a760a/phase7_real_event_report.md`

Final summary:
- event assets: `9`
- evaluation rows: `27`
- evidence level coverage: `level_3` only for current frozen event set
- default promotion decision: `phase5_default_real_event_leader`

Model-level mean proxy metrics over current real-event set:
- Phase 4 best graph: hidden MAE `1363.7538`, trend correlation `-0.7229`
- Phase 5 default: hidden MAE `85.7863`, trend correlation `-0.7112`
- Phase 6 feature_only: hidden MAE `77.1144`, trend correlation `-0.7335`

## Interpretation

- Phase 7 does produce usable real-event validation evidence.
- Under the current decision rule, Phase 5 is the real-event leader because its average trend correlation is slightly better than Phase 6.
- Under proxy hidden-node MAE alone, Phase 6 is lower than Phase 5 on the current event set.
- These results should not be read as full-network real-world accuracy claims because the evidence level is limited and station-local reference curves are only partial truth.

## Remaining Boundaries

- Current event set is still small and evidence-limited.
- Current real-event reference is station-local disturbance, not full-grid GIC truth.
- Peak timing numbers are currently large and should be interpreted as failure-case evidence, not deployment-grade timing quality.
- Phase 8 should build on these assets rather than redefining the Phase 5/6 frozen baselines.
