# Decision Record 0005: Phase 5 Main Model Design

## Status
Accepted for the initial Phase 5 implementation.

## Decision
Phase 5 uses a modular `InputEncoder -> TemporalEncoder -> GraphBackbone -> PhysicsFusion -> TaskHeads -> LossComposer` structure.
The implementation keeps both physics-feature input and residual formulation available, while the default dev profile currently uses normalized physics input without residual addition.

## Rationale
- `GRU + graph backbone` was chosen because it is simpler and easier to ablate than a full temporal graph transformer.
- Physics fusion was chosen because Phase 5 must integrate physical prior information while staying comparable with Phase 4.
- Residual mode is implemented because it is the clearest physics-informed correction path, but the current small benchmark favored input-only fusion as the default profile.
- The default auxiliary task is hotspot classification because it is the smallest useful extension beyond mean regression error.
- The default loss keeps regression primary and treats hotspot loss and physics penalty as configurable add-ons.

## Alternatives Considered
- Pure graph model without temporal module: kept as the `no_temporal` ablation instead of the default.
- Physics penalty only: rejected as the default because it is harder to interpret and easier to overweight.
- Risk ranking as the first auxiliary head: postponed because hotspot labels are clearer in the current data regime.

## Consequences
- Phase 5 can compare directly with the Phase 4 best baseline on the same graph-ready dataset.
- Every major enhancement remains switchable for ablation.
- The model leaves stable interfaces for Phase 6 without introducing KG logic early.
