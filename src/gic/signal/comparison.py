from __future__ import annotations

from typing import Any

from gic.signal.schema import FrontendComparisonReport, FrontendResult


def _score_result(result: FrontendResult, comparison_config: dict[str, Any]) -> float:
    weights = comparison_config.get("score_weights", {})
    metrics = result.quality_metrics
    score = 0.0
    if metrics.get("quasi_dc_correlation") is not None:
        score += float(weights.get("quasi_dc_correlation", 3.0)) * float(metrics["quasi_dc_correlation"])
    if metrics.get("correlation_to_reference") is not None:
        score += float(weights.get("correlation_to_reference", 2.0)) * float(metrics["correlation_to_reference"])
    if metrics.get("snr_improvement_db") is not None:
        score += float(weights.get("snr_improvement_db", 0.1)) * float(metrics["snr_improvement_db"])
    if metrics.get("rmse_to_reference") is not None:
        score -= float(weights.get("rmse_to_reference", 0.5)) * float(metrics["rmse_to_reference"])
    if metrics.get("peak_error") is not None:
        score -= float(weights.get("peak_error", 0.2)) * float(metrics["peak_error"])
    score -= float(weights.get("runtime_ms", 0.001)) * float(metrics.get("runtime_ms", 0.0))
    score -= float(weights.get("residual_highfreq_ratio", 1.0)) * float(metrics.get("residual_highfreq_ratio", 0.0))
    if result.status == "warning":
        score -= float(weights.get("warning_penalty", 0.25))
    if result.status == "failed":
        score -= float(weights.get("failure_penalty", 2.0))
    return float(score)


def build_comparison_report(
    *,
    sample_id: str,
    results: list[FrontendResult],
    comparison_config: dict[str, Any],
) -> FrontendComparisonReport:
    priority = comparison_config.get("default_method_priority", [])
    rows: list[dict[str, Any]] = []
    for result in results:
        score = _score_result(result, comparison_config)
        rows.append(
            {
                "method_name": result.method_name,
                "status": result.status,
                "score": score,
                "runtime_ms": result.quality_metrics.get("runtime_ms"),
                "correlation_to_reference": result.quality_metrics.get("correlation_to_reference"),
                "quasi_dc_correlation": result.quality_metrics.get("quasi_dc_correlation"),
                "rmse_to_reference": result.quality_metrics.get("rmse_to_reference"),
                "snr_improvement_db": result.quality_metrics.get("snr_improvement_db"),
            }
        )

    def _priority_index(method_name: str) -> int:
        return priority.index(method_name) if method_name in priority else len(priority)

    rows.sort(key=lambda item: (-float(item["score"]), _priority_index(str(item["method_name"])), str(item["method_name"])))
    ranking = [str(item["method_name"]) for item in rows]
    default_method = ranking[0] if ranking else ""
    return FrontendComparisonReport(
        comparison_id=f"{sample_id}_frontend_comparison",
        sample_id=sample_id,
        methods=[result.method_name for result in results],
        ranking=ranking,
        default_method=default_method,
        summary_table=rows,
        notes="Comparison built from unified frontend metrics and configured score weights.",
    )
