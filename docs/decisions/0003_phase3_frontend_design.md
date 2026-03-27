# Decision 0003: Phase 3 Frontend Design

## Decision

Phase 3 keeps the signal frontend decoupled from downstream graph and physics-informed models. All frontend methods must emit the same result schema and must be comparable under the same metrics.

## Why Decoupled

- Frontend methods need to be swapped and compared without changing model code.
- Phase 4 and Phase 5 should consume signal-ready data, not private method outputs.
- This keeps failures and method-specific tradeoffs visible.

## Baseline Families Chosen

- raw baseline for no-frontend reference
- low-frequency baseline for stability and interpretability
- FastICA baseline for multi-channel source separation
- sparse baseline for stronger noise suppression candidate behavior

## Why Keep No-Frontend Baseline

Without a raw baseline, Phase 3 cannot show whether a frontend actually helps or only changes the signal.

## Default Recommendation Rule

The default frontend is chosen from a comparison report using reference fidelity, runtime, residual energy, and a stable priority rule. The project does not hard-code FastICA as the default method.
