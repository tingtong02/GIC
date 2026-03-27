# Source Usage Matrix

| Source Name | Type | Purpose | Intended Use | Status | Planned Phase | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `matpower_case118` | grid_case | baseline grid case ingestion | yes | active | Phase 1 / 2 / 4 | 当前以本地 MATPOWER 风格样例先跑通 |
| `uiuc_150_bus_candidate` | grid_case | future extended benchmark | yes | candidate | Phase 1 / 2 / 7 | 仅登记，未接入 |
| `sample_geomagnetic_series` | geomagnetic_timeseries | minimal geomagnetic driver ingestion | yes | active | Phase 1 / 3 / 7 | 本地 CSV 样例 |
| `supermag_reference` | geomagnetic_timeseries | future real geomagnetic ingestion | yes | planned | Phase 1 / 3 / 7 | 仅登记，未自动化 |
| `intermagnet_reference` | geomagnetic_timeseries | future cross-validation source | yes | planned | Phase 1 / 3 / 7 | 仅登记，未自动化 |
| `noaa_geoelectric_reference` | geoelectric_timeseries | future geoelectric forcing ingestion | yes | candidate | Phase 1 / 2 / 7 | 仅登记，未接入 |
| `paper_gic_observation_reference` | gic_observation | future external validation reference | yes | reference_only | Phase 1 / 7 | schema 与来源占位 |
