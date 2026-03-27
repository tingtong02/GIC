# Signal Feature Schema

## FrontendResult

Required fields:

- `result_id`
- `sample_id`
- `method_name`
- `method_version`
- `config_hash`
- `denoised_series`
- `quasi_dc_series`
- `feature_set`
- `quality_metrics`
- `status`

## SignalFeatureSet

Required fields:

- `feature_id`
- `window_definition`
- `summary_statistics`
- `peak_features`
- `trend_features`
- `spectral_features`
- `quality_flags`

## signal-ready Export Layout

Standard export root:

```text
data/processed/signal_ready/
  timeseries/
  features/
  manifests/
  reports/
  comparisons/
```

Each exported method result includes:

- time-series payload with denoised and quasi-DC series
- feature payload
- quality report
- manifest with source sample and config hash

## Manifest Fields

- `sample_id`
- `method_name`
- `config_hash`
- `source_name`
- `generated_at_utc`
- `paths`
