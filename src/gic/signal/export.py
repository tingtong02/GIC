from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gic.signal.postprocess import build_quality_report
from gic.signal.schema import FrontendComparisonReport, FrontendResult, SignalSample, signal_to_dict
from gic.utils.paths import ensure_directory


def _export_root(project_root: Path, signal_config: dict[str, Any]) -> Path:
    return ensure_directory(project_root / signal_config["output_root"])


def export_frontend_result(
    *,
    project_root: Path,
    signal_config: dict[str, Any],
    signal_sample: SignalSample,
    result: FrontendResult,
) -> dict[str, str]:
    root = _export_root(project_root, signal_config)
    timeseries_root = ensure_directory(root / "timeseries")
    features_root = ensure_directory(root / "features")
    manifests_root = ensure_directory(root / "manifests")
    reports_root = ensure_directory(root / "reports")
    base_name = f"{signal_sample.sample_id}_{result.method_name}"
    timeseries_path = timeseries_root / f"{base_name}.json"
    features_path = features_root / f"{base_name}.json"
    report_path = reports_root / f"{base_name}_quality.json"
    manifest_path = manifests_root / f"{base_name}.manifest.json"

    timeseries_payload = {
        "sample_id": signal_sample.sample_id,
        "method_name": result.method_name,
        "denoised_series": signal_to_dict(result.denoised_series),
        "quasi_dc_series": signal_to_dict(result.quasi_dc_series),
        "metadata": result.metadata,
    }
    timeseries_path.write_text(json.dumps(timeseries_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    features_path.write_text(json.dumps(signal_to_dict(result.feature_set), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_path.write_text(
        json.dumps(signal_to_dict(build_quality_report(result)), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    manifest_payload: dict[str, Any] = {
        "sample_id": signal_sample.sample_id,
        "method_name": result.method_name,
        "config_hash": result.config_hash,
        "source_name": signal_sample.source_name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "paths": {
            "timeseries": str(timeseries_path),
            "features": str(features_path),
            "quality_report": str(report_path),
            "manifest": str(manifest_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_payload["paths"]


def export_comparison_report(
    *,
    project_root: Path,
    signal_config: dict[str, Any],
    comparison_report: FrontendComparisonReport,
) -> str:
    root = _export_root(project_root, signal_config)
    comparison_root = ensure_directory(root / "comparisons")
    destination = comparison_root / f"{comparison_report.sample_id}_comparison.json"
    destination.write_text(json.dumps(signal_to_dict(comparison_report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(destination)
