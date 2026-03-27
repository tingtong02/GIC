# Signal Frontend Overview

Phase 3 keeps the signal frontend fully decoupled from downstream models.

Implemented frontends:
- `raw_baseline`
- `lowfreq_baseline`
- `fastica` via `sklearn.decomposition.FastICA`
- `sparse_denoise` via `MiniBatchDictionaryLearning + sparse_encode`
- `legacy_sparse_baseline` for regression only

Comparison policy:
- Synthetic benchmark uses `synthetic_score_policy`
- Real-event benchmark uses `real_data_score_policy`

Default recommendation policy:
- `default_for_training` comes from the synthetic benchmark
- `default_for_real_event_benchmark` is informational until promotion thresholds are met
