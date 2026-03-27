# Physics Fusion Design

## How Physics Information Enters The Model
- Phase 5 reads the graph-ready physics proxy feature `physics.adjacent_induced_abs_sum` for every node.
- The default path uses normalized physics feature input.
- Residual learning remains implemented and configurable, but it is not the default dev profile on the current small benchmark.

## Residual Formulation
- Optional formulation: `prediction = learned_residual + physics_baseline_proxy`.
- This path is kept because it is the clearest physics-informed correction formulation, and it remains part of the ablation-ready interface.

## Physics Penalty
- The physics penalty is optional and fully configurable.
- Available penalty: MAE or MSE between regression prediction and the physics baseline proxy.
- Weight is controlled by `loss.physics_penalty_weight` and can be disabled entirely.

## Why This Design
- Feature input keeps the architecture close to Phase 4 and stable for fair comparison.
- Residual learning is preserved as a supported path, but the current dev benchmark showed that forcing it as the default was unstable.
- A soft penalty avoids the Phase 5 anti-pattern of making physical consistency a fixed, non-negotiable rule.

## Applicability Boundaries
- Feature-input mode is the current stable default when the physics proxy is informative but not strong enough to anchor residual learning.
- No-physics ablation should stay available because the proxy can be biased or too coarse in some scenarios.
- If later phases introduce richer physical state or KG augmentation, the current physics-fusion interface should stay modular instead of being rewritten in-place.
