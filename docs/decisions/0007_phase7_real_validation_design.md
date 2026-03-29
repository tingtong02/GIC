# Decision 0007: Phase 7 Real Validation Design

## Status

Accepted for Phase 7 implementation.

## Context

The project needs a real-event validation layer, but currently has only limited local geomagnetic observations and no network-wide GIC truth labels.

## Decision

We use a layered real-event validation design:

- fixed INTERMAGNET smoke windows as the initial real-event set
- explicit evidence levels 1-4
- proxy numeric consistency against real-driven physics labels kept separate from real-world evidence conclusions
- grouped reporting for main / generalization / boundary events

## Rationale

This keeps the validation pipeline scientifically honest while still allowing Phase 4/5/6 model families to run under real geomagnetic drivers.

## Consequences

- Phase 7 can produce reproducible real-event evaluation assets immediately from local data.
- Stronger claims will still require richer direct measurements in later stages.
