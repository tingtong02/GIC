# Reproduction Guide

## Default Final Path

Run the final default integration path:

```bash
PYTHONPATH=src conda run -n GIC_env python -m gic.cli.main run-final-default --config configs/final/final_default.yaml --project-root /home/user/projects/GIC
```

## Final Reproduction Path

Run the reproducible export path:

```bash
PYTHONPATH=src conda run -n GIC_env python -m gic.cli.main run-final-reproduction --config configs/final/final_reproduction.yaml --project-root /home/user/projects/GIC
```

## Final Real-Event Refresh

```bash
PYTHONPATH=src conda run -n GIC_env python -m gic.cli.main run-final-real-eval --config configs/final/final_real_eval.yaml --project-root /home/user/projects/GIC
```

## Check-Only Mode

All final CLI entries support `--check-only` for frozen-asset verification without running the active synthetic evaluation path.
