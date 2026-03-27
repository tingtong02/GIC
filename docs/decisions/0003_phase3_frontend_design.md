# 0003 Phase 3 Frontend Design

Decisions:
- Keep the signal frontend independent from Phase 4 model code.
- Upgrade `fastica` to `sklearn.FastICA` instead of keeping a pure-`numpy` prototype.
- Upgrade `sparse_denoise` to dictionary learning with sparse coding; keep the old shrinkage baseline only for regression.
- Distinguish synthetic-reference metrics from reference-absent metrics.
- Freeze `default_for_training` to the synthetic benchmark until real-event promotion thresholds are satisfied.
