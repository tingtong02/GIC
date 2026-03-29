# Final Results Summary

## Synthetic Benchmark

The frozen broader synthetic benchmark remains anchored on the Phase 4 graph baseline, the Phase 5 default main model, and the Phase 6 `feature_only` KG-enhanced variant.

Current frozen hidden-node MAE values:
- Phase 4 graph baseline: `22.175137162208557`
- Phase 5 default: `7.73746395111084`
- Phase 6 feature_only: `5.947530508041382`

## Real Event Validation

The frozen Phase 7 report keeps the real-event decision conservative. The current decision is `phase5_default_real_event_leader`, which means the final default path remains Phase 5 even though Phase 6 retains lower proxy hidden-node MAE on the same event set.

## Final Default Decision

- Final default path: `without_kg`
- Optional final variant: `with_kg` using Phase 6 `feature_only`
- Evidence basis: Phase 7 real-event validation decision plus frozen synthetic superiority of Phase 5/Phase 6 over Phase 4
