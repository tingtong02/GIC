# Decision Record 0008: Phase 8 Final Integration

## Decision

Freeze the final integrated system around the Phase 5 default checkpoint as the main default path and keep the Phase 6 `feature_only` checkpoint as an optional KG-enabled branch.

## Rationale

- Phase 5 and Phase 6 both outperform the Phase 4 graph baseline on the frozen synthetic benchmark.
- Phase 7 real-event validation currently promotes the Phase 5 default path under the conservative decision rule.
- KG remains useful and should stay available, but current evidence is not strong enough to silently replace the default path.

## Consequences

- Final CLI must support `with-kg` and `without-kg` behavior.
- Final documentation must state that KG is optional rather than universally promoted.
- Later phases should compare against these frozen references instead of redefining the baseline.
