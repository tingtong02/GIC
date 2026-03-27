from __future__ import annotations

import math
from typing import Any

from gic.signal.schema import FrontendComparisonReport, FrontendResult


def _score_metric(weights: dict[str, Any], metrics: dict[str, Any], key: str, invert: bool = False) -> float:
    value = metrics.get(key)
    if value is None:
        return 0.0
    value = float(value)
    if not math.isfinite(value):
        return 0.0
    weight = float(weights.get(key, 0.0))
    score = weight * value
    return -score if invert else score


def _score_result(result: FrontendResult, comparison_config: dict[str, Any], benchmark_type: str) -> float:
    if benchmark_type == 'synthetic':
        weights = comparison_config.get('synthetic_score_policy', comparison_config.get('score_weights', {}))
        metrics = dict(result.quality_metrics.get('synthetic_reference_metrics', {}))
        metrics['runtime_ms'] = result.quality_metrics.get('runtime_ms')
        metrics['residual_highfreq_ratio'] = result.quality_metrics.get('residual_highfreq_ratio')
        score = 0.0
        score += _score_metric(weights, metrics, 'quasi_dc_correlation')
        score += _score_metric(weights, metrics, 'correlation_to_reference')
        score += _score_metric(weights, metrics, 'snr_improvement_db')
        score += _score_metric(weights, metrics, 'rmse_to_reference', invert=True)
        score += _score_metric(weights, metrics, 'peak_error', invert=True)
        score += _score_metric(weights, metrics, 'runtime_ms', invert=True)
        score += _score_metric(weights, metrics, 'residual_highfreq_ratio', invert=True)
    else:
        weights = comparison_config.get('real_data_score_policy', {})
        metrics = dict(result.quality_metrics.get('reference_absent_metrics', {}))
        metrics['runtime_ms'] = result.quality_metrics.get('runtime_ms')
        metrics['residual_highfreq_ratio'] = result.quality_metrics.get('residual_highfreq_ratio')
        score = 0.0
        score += _score_metric(weights, metrics, 'trend_alignment_to_observed')
        score += _score_metric(weights, metrics, 'denoised_observed_correlation')
        score += _score_metric(weights, metrics, 'peak_preservation_ratio')
        score += _score_metric(weights, metrics, 'stability_score')
        score += _score_metric(weights, metrics, 'quasi_dc_variance_ratio')
        score += _score_metric(weights, metrics, 'runtime_ms', invert=True)
        score += _score_metric(weights, metrics, 'residual_highfreq_ratio', invert=True)
    if result.status == 'warning':
        score -= float(weights.get('warning_penalty', 0.25))
    if result.status == 'failed':
        score -= float(weights.get('failure_penalty', 2.0))
    return float(score)


def build_comparison_report(
    *,
    sample_id: str,
    results: list[FrontendResult],
    comparison_config: dict[str, Any],
    benchmark_type: str | None = None,
    default_scope: str | None = None,
    promotion_status: str | None = None,
    promotion_reason: str | None = None,
) -> FrontendComparisonReport:
    resolved_benchmark_type = benchmark_type or (
        'synthetic' if any(result.quality_metrics.get('reference_available') for result in results) else 'real_event'
    )
    priority = comparison_config.get('default_method_priority', [])
    rows: list[dict[str, Any]] = []
    for result in results:
        score = _score_result(result, comparison_config, resolved_benchmark_type)
        rows.append(
            {
                'method_name': result.method_name,
                'status': result.status,
                'score': score,
                'runtime_ms': result.quality_metrics.get('runtime_ms'),
                'correlation_to_reference': result.quality_metrics.get('correlation_to_reference'),
                'quasi_dc_correlation': result.quality_metrics.get('quasi_dc_correlation'),
                'rmse_to_reference': result.quality_metrics.get('rmse_to_reference'),
                'snr_improvement_db': result.quality_metrics.get('snr_improvement_db'),
                'trend_alignment_to_observed': result.quality_metrics.get('reference_absent_metrics', {}).get('trend_alignment_to_observed'),
                'stability_score': result.quality_metrics.get('reference_absent_metrics', {}).get('stability_score'),
                'benchmark_type': resolved_benchmark_type,
            }
        )

    def _priority_index(method_name: str) -> int:
        return priority.index(method_name) if method_name in priority else len(priority)

    rows.sort(key=lambda item: (-float(item['score']), _priority_index(str(item['method_name'])), str(item['method_name'])))
    ranking = [str(item['method_name']) for item in rows]
    default_method = ranking[0] if ranking else ''
    resolved_scope = default_scope or ('training' if resolved_benchmark_type == 'synthetic' else 'real_event_benchmark')
    resolved_status = promotion_status or ('ready' if resolved_scope == 'training' else 'provisional')
    resolved_reason = promotion_reason or (
        'Synthetic benchmark winner becomes the current training default.'
        if resolved_scope == 'training'
        else 'Real-event benchmark is informational until promotion thresholds are met.'
    )
    return FrontendComparisonReport(
        comparison_id=f'{sample_id}_frontend_comparison',
        sample_id=sample_id,
        methods=[result.method_name for result in results],
        ranking=ranking,
        default_method=default_method,
        summary_table=rows,
        benchmark_type=resolved_benchmark_type,
        default_scope=resolved_scope,
        promotion_status=resolved_status,
        promotion_reason=resolved_reason,
        notes='Comparison built from unified frontend metrics and benchmark-specific score policies.',
    )
