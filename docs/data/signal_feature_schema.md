# Signal Feature Schema

`FrontendResult.quality_metrics` now separates:
- `synthetic_reference_metrics`
- `reference_absent_metrics`

This prevents real-event comparisons from pretending to have ground-truth reconstruction error.

Real-event datasets currently come from Phase 3 INTERMAGNET smoke ingestion for:
- `BOU`
- `FRD`
- `OTT`
