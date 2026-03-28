from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run_cli(project_root: Path, config_path: Path) -> dict[str, Any]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = "src" if not pythonpath else f"src:{pythonpath}"
    proc = subprocess.run(
        [sys.executable, "-m", "gic.cli.main", "train-main-model", "--config", str(config_path.resolve()), "--project-root", str(project_root.resolve())],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"CLI failed for {config_path}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    stdout = proc.stdout.strip()
    payload = json.loads(stdout)
    payload["stderr"] = proc.stderr
    return payload


def _summary(name: str, payload: dict[str, Any]) -> dict[str, Any]:
    hidden = payload["test_metrics"]["hidden_only"]
    signal_summary = payload.get("signal_summary", {})
    return {
        "candidate": name,
        "run_id": payload.get("run_id"),
        "checkpoint_path": payload.get("checkpoint_path"),
        "metrics_report_path": payload.get("metrics_report_path"),
        "hidden_mae": hidden.get("mae"),
        "hidden_rmse": hidden.get("rmse"),
        "hidden_correlation": hidden.get("correlation"),
        "active_signal_feature_count": signal_summary.get("active_feature_count"),
        "dropped_signal_feature_count": signal_summary.get("dropped_zero_variance_count"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default="/home/user/projects/GIC")
    parser.add_argument("--configs", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    results: list[dict[str, Any]] = []
    for index, item in enumerate(args.configs, start=1):
        config_path = (project_root / item).resolve() if not Path(item).is_absolute() else Path(item).resolve()
        name = config_path.stem
        print(f"[followup {index}/{len(args.configs)}] {name}", file=sys.stderr, flush=True)
        payload = _run_cli(project_root, config_path)
        results.append(_summary(name, payload))
    results.sort(key=lambda row: float(row["hidden_mae"]))
    output_path = Path(args.output).resolve()
    output_path.write_text(json.dumps({"results": results}, indent=2) + "\n")
    print(json.dumps({"status": "ok", "output_path": str(output_path), "best_candidate": results[0]["candidate"] if results else None}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
