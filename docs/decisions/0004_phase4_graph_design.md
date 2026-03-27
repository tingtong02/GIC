# 0004 Phase 4 Graph Design

## Status
Accepted

## Decision
Phase 4 uses `bus` as the primary graph node type and exports graph-ready samples as standalone files under `data/processed/graph_ready/` before any model training.

## Rationale
- Bus nodes match the current Phase 1/2 topology and Phase 2 bus-level labels directly.
- A standalone graph-ready layer prevents training scripts from owning hidden graph-construction logic.
- A non-graph baseline must exist later in Phase 4 so graph gains can be evaluated honestly.
- The first graph-ready pass keeps the graph single-type and electrically connected, leaving hetero-graph extensions for Phase 5 or later.

## Consequences
- Transformer-level targets remain available through label metadata rather than a separate primary node type.
- Signal-ready features are currently injected as reusable global summaries, not as node-specific learned frontends.
- Phase 4 model work should build on this exported graph-ready layer instead of bypassing it.
