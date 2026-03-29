# GIC

Unified research system for geomagnetically induced current reconstruction.

## Final Default Path

The frozen final default runtime path is the Phase 5 default checkpoint without KG. The frozen Phase 6 `feature_only` checkpoint is retained as an optional KG-enabled variant.

## Final Config Bundle

- `configs/final/final_default.yaml`
- `configs/final/final_reproduction.yaml`
- `configs/final/final_real_eval.yaml`
- `configs/final/final_with_kg.yaml`
- `configs/final/final_without_kg.yaml`

## Main Commands

```bash
PYTHONPATH=src conda run -n GIC_env python -m gic.cli.main run-final-default --config configs/final/final_default.yaml --project-root /home/user/projects/GIC
PYTHONPATH=src conda run -n GIC_env python -m gic.cli.main run-final-reproduction --config configs/final/final_reproduction.yaml --project-root /home/user/projects/GIC
PYTHONPATH=src conda run -n GIC_env python -m gic.cli.main run-final-real-eval --config configs/final/final_real_eval.yaml --project-root /home/user/projects/GIC
```

All final CLI entries support `--with-kg`, `--without-kg`, `--check-only`, and `--output-dir`.

## Frozen Evidence Summary

- Phase 4 broader best graph baseline hidden-node MAE: `21.21492975950241`
- Phase 5 frozen default broader hidden-node MAE: `7.73746395111084`
- Phase 6 frozen `feature_only` broader hidden-node MAE: `5.947530508041382`
- Phase 7 frozen real-event decision: `phase5_default_real_event_leader`

## Final Documentation

- `docs/architecture/final_system_overview.md`
- `docs/evaluation/final_results_summary.md`
- `docs/evaluation/final_limitations.md`
- `docs/reproduction/reproduction_guide.md`
- `docs/roadmap/final_handoff_summary.md`
