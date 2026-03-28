# 0006 Phase 6 KG Design

## Status

Accepted.

## Decision

Phase 6 starts with a minimal, task-scoped KG rather than a large standalone platform.

## Rationale

- Phase 5 is already frozen and should remain the non-KG control.
- Feature-level enhancement is the lowest-risk integration path for fair comparison.
- Lightweight rules for assumptions, quality flags, and missingness improve traceability without requiring a reasoning engine.
- A small explicit schema keeps entity and relation scope bounded and testable.

## Consequences

- Phase 6 assets can be built from current graph-ready, physics-ready, signal-ready, and metadata outputs.
- The first Phase 6 deliverable is a reproducible KG export and feature derivation path.
- Relation-aware deep fusion remains a later extension, not the starting point.
