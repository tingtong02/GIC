# Phase 3 Handoff - 2026-03-27

## 1. Current Status

Project progress is currently stable through Phase 3 hardening.

Completed scope:
- Phase 0 scaffold and runtime baseline
- Phase 1 data schema, registry, parser, converter, validation, and data docs
- Phase 2 physics baseline, scenario generation, label export, and validation
- Phase 3 signal frontend baseline, method comparison, signal-ready export, and risk-hardening follow-up

This handoff focuses on the latest Phase 3 hardening work.

## 2. What Was Added In The Latest Phase 3 Hardening Pass

### 2.1 Scientific dependency baseline

The project now declares the following Phase 3 scientific dependencies in `pyproject.toml`:
- `scipy>=1.13,<2`
- `scikit-learn>=1.5,<2`
- `pandas>=2.2,<3`

These are now treated as the minimum scientific stack for the Phase 3 production-style frontend baseline.

### 2.2 Frontend method upgrades

The signal frontend layer keeps the same unified interface but the internal implementations were upgraded:
- `fastica` now uses `sklearn.decomposition.FastICA`
- `sparse_denoise` now uses `MiniBatchDictionaryLearning + sparse_encode`
- `legacy_sparse_baseline` is preserved for regression only
- `raw_baseline` now correctly handles missing values through the shared preprocessing path
- `lowfreq_baseline` remains the stable fallback baseline

Relevant code:
- `src/gic/signal/methods/fastica_frontend.py`
- `src/gic/signal/methods/sparse_frontend.py`
- `src/gic/signal/methods/raw_baseline.py`
- `src/gic/signal/metrics.py`
- `src/gic/signal/comparison.py`
- `src/gic/signal/preprocess.py`
- `src/gic/signal/schema.py`

### 2.3 Metric split for reference vs non-reference scenarios

`FrontendResult.quality_metrics` now separates two evaluation branches:
- `synthetic_reference_metrics`
- `reference_absent_metrics`

This was introduced to avoid treating real geomagnetic observations as if they had ground-truth denoising labels.

Synthetic benchmark behavior:
- uses reference-aware metrics such as correlation, RMSE, quasi-DC correlation, and SNR improvement

Real-event benchmark behavior:
- uses trend alignment, observed-signal consistency, peak preservation, variance ratio, and stability metrics

### 2.4 Comparison policy split and dual default logic

Comparison now distinguishes:
- `synthetic_score_policy`
- `real_data_score_policy`

The recommendation system now reports two defaults instead of one:
- `default_for_training`
- `default_for_real_event_benchmark`

Current policy:
- training default is determined only by the synthetic benchmark
- real-event benchmark remains informational until promotion thresholds are met

Current promotion threshold:
- at least 3 stations
- at least 3 event windows
- at least 2 scoring-policy agreements

## 3. INTERMAGNET Data Ingestion Status

### 3.1 Raw archive support

The project can now ingest the local INTERMAGNET annual archive already present in the repo:
- `data/raw/geomagnetic/intermagnet_mag2020_def2020/`

Supported stations in this first pass:
- `BOU`
- `FRD`
- `OTT`

Supported raw inputs in v1:
- `.bin` is the primary numeric input
- `readme.*` is parsed for station metadata
- `.blv` and `.dka` are recorded as provenance only

### 3.2 Data layer extension

New implementation was added here:
- `src/gic/data/parsers/intermagnet_parser.py`
- `src/gic/data/converters/intermagnet_converter.py`
- `src/gic/data/loaders/timeseries_loader.py`
- `src/gic/data/schema.py`

### 3.3 Registry status

The registry now contains:
- annual standardized station datasets for `BOU / FRD / OTT`
- a fixed smoke-test event window dataset for each station

Smoke-test window used in this pass:
- `2020-09-01T00:00:00Z` to `2020-09-02T00:00:00Z`

Relevant registry files:
- `data/registry/data_sources.yaml`
- `data/registry/datasets.yaml`

### 3.4 Interim conversion outputs

The Phase 1 conversion command now successfully writes standardized INTERMAGNET assets to:
- `data/interim/timeseries/intermagnet_bou_2020_year.json`
- `data/interim/timeseries/intermagnet_frd_2020_year.json`
- `data/interim/timeseries/intermagnet_ott_2020_year.json`
- `data/interim/timeseries/intermagnet_bou_2020_sep01_smoke.json`
- `data/interim/timeseries/intermagnet_frd_2020_sep01_smoke.json`
- `data/interim/timeseries/intermagnet_ott_2020_sep01_smoke.json`

## 4. CLI / Workflow Status

The existing CLI was extended without adding new top-level command names.

Still supported and now expanded:
- `data-convert-sample`
- `signal-validate-input`
- `signal-compare-frontends`
- `signal-build-report`

Latest workflow now supports:
1. convert INTERMAGNET raw archive through the standard data layer
2. validate a real-event smoke dataset
3. compare multiple frontends on that real dataset
4. build a dual-benchmark report covering both synthetic and real-event benchmarks

## 5. Current Benchmark Outcome

### 5.1 Synthetic benchmark

Current synthetic benchmark winner:
- `fastica`

This is the current:
- `default_for_training`

### 5.2 Real-event benchmark

Current real-event benchmark winner on the current smoke coverage:
- `raw_baseline`

This is the current:
- `default_for_real_event_benchmark`

Important caveat:
- this result is still `provisional`
- it does not override the training default
- current real benchmark coverage is only 3 stations and 1 event window

## 6. Validation And Test Results

### 6.1 Manual command validation completed

The following workflows were run successfully:
- dependency import check for `scipy / sklearn / pandas`
- Phase 1 data conversion with INTERMAGNET datasets active
- Phase 3 signal input validation on `intermagnet_bou_2020_sep01_smoke`
- Phase 3 frontend comparison on `intermagnet_bou_2020_sep01_smoke`
- Phase 3 dual-benchmark report generation

### 6.2 Test status

Latest full regression result:
- `41 passed, 2 warnings in 30.08s`

Warnings observed:
- `torch` NVML warning in environment validation
- `FastICA` convergence warning on at least one real dataset during benchmark generation

Neither warning currently blocks Phase 3 functionality.

## 7. Known Risks / Open Items

### 7.1 FastICA stability on real data

Status:
- still not fully stable on all real-event inputs
- warning is explicit and does not silently fallback

Suggested next step:
- tune `max_iter`, `tol`, and component selection logic on longer real-event windows

### 7.2 Real benchmark coverage is still too small

Status:
- only one event window is registered for the real benchmark

Impact:
- real-event recommendation remains provisional
- cannot be promoted to project-wide default logic yet

Suggested next step:
- add at least 2 more event windows across the same 3 stations or equivalent coverage

### 7.3 INTERMAGNET parser is a v1 implementation

Status:
- numeric parsing is stable enough for the current smoke path
- `.bin` is supported as primary numeric input
- `.blv` and `.dka` are tracked only as provenance

Suggested next step:
- add stronger format validation and unit documentation if the project later relies more heavily on INTERMAGNET data

## 8. Recommended Next Actions For The Next Developer

Priority order:
1. keep Phase 3 boundary and expand real-event benchmark coverage
2. add more real event windows before changing any global default recommendation rule
3. only after that, decide whether Phase 3 needs one more hardening pass or if the project should move to Phase 4

Concrete next tasks:
- register 2 or more additional INTERMAGNET event windows
- rerun `signal-build-report`
- check whether real benchmark ranking remains stable across events
- if stability improves, revisit promotion logic thresholds
- if Phase 3 is accepted, start Phase 4 only after re-reading `docs/GIC_project_phase_roadmap_v1.md` and `docs/phase_4_detailed_plan.md`

## 9. Important Files To Review First

If someone new takes over, these are the highest-value entry points:
- `src/gic/cli/main.py`
- `src/gic/signal/comparison.py`
- `src/gic/signal/metrics.py`
- `src/gic/signal/methods/fastica_frontend.py`
- `src/gic/signal/methods/sparse_frontend.py`
- `src/gic/data/parsers/intermagnet_parser.py`
- `src/gic/data/converters/intermagnet_converter.py`
- `configs/phase3/phase3_dev.yaml`
- `data/registry/datasets.yaml`
- `docs/models/signal_frontend_overview.md`
- `docs/data/signal_feature_schema.md`

## 10. Handoff Conclusion

As of 2026-03-27, the project is in a good Phase 3 state:
- unified frontend framework is intact
- upgraded scientific backends are in place
- INTERMAGNET smoke ingestion is working
- signal-ready outputs are generated for both synthetic and real-event inputs
- benchmark logic now distinguishes training default from real-event benchmark default
- full tests pass

The main remaining gap is not basic functionality anymore, but benchmark coverage and stability on more real-event windows.
