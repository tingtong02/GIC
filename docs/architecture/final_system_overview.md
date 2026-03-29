# Final System Overview

## Default System Path

The final integrated GIC system uses the frozen Phase 5 default checkpoint as the default predictive path and retains the Phase 6 `feature_only` KG-enhanced variant as an optional branch.

## End-to-End Pipeline

1. Load frozen config bundle from `configs/final/`
2. Resolve frozen reports, checkpoints, datasets, and real-eval assets
3. Run synthetic evaluation on the frozen default or optional KG branch
4. Reuse or refresh Phase 7 real-event validation
5. Export final summary, visuals, and casebook assets

## Frozen References

- Phase 5 default frozen checkpoint
- Phase 6 `feature_only` frozen checkpoint
- Phase 7 frozen real-event validation report

## Outputs

- Final summary JSON / Markdown
- SVG visuals for synthetic comparison, real comparison, timeline, failure cases, and KG summary
- Final casebook JSON / Markdown
- Final handoff-oriented documentation
