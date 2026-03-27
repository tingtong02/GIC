# GIC

Phase-structured research scaffold for geomagnetically induced current reconstruction.

Current baseline status:
- Phase 0 scaffold, Phase 1 data infrastructure, Phase 2 physics baseline, and Phase 3 signal frontend are implemented in lightweight research form.
- Phase 3 now depends on a minimal scientific stack: `scipy`, `scikit-learn`, and `pandas`.
- The current `default_for_training` recommendation is chosen from the synthetic benchmark.
- Real-event benchmark conclusions are provisional until at least 3 stations, 3 event windows, and 2 scoring-policy agreements are available.

Important paths:
- `configs/phase3/phase3_dev.yaml`: active Phase 3 config
- `data/raw/geomagnetic/intermagnet_mag2020_def2020/`: preserved INTERMAGNET raw archive
- `data/processed/signal_ready/`: exported frontend outputs and comparison reports
