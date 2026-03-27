#!/usr/bin/env bash
set -euo pipefail
PYTHONPATH=src python -m gic.cli.main run --config configs/phase0/phase0_dev.yaml "$@"
