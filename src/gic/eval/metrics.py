from __future__ import annotations

import math
from typing import Any



def compute_regression_metrics(predictions: list[float], targets: list[float]) -> dict[str, float]:
    if len(predictions) != len(targets):
        raise ValueError('Predictions and targets must have the same length')
    if not predictions:
        return {'mae': 0.0, 'rmse': 0.0, 'correlation': 0.0}
    absolute_errors = [abs(prediction - target) for prediction, target in zip(predictions, targets)]
    squared_errors = [(prediction - target) ** 2 for prediction, target in zip(predictions, targets)]
    mean_prediction = sum(predictions) / len(predictions)
    mean_target = sum(targets) / len(targets)
    centered_prediction = [prediction - mean_prediction for prediction in predictions]
    centered_target = [target - mean_target for target in targets]
    numerator = sum(prediction * target for prediction, target in zip(centered_prediction, centered_target))
    prediction_norm = math.sqrt(sum(item * item for item in centered_prediction))
    target_norm = math.sqrt(sum(item * item for item in centered_target))
    denominator = prediction_norm * target_norm
    correlation = numerator / denominator if denominator > 0 else 0.0
    return {
        'mae': sum(absolute_errors) / len(absolute_errors),
        'rmse': math.sqrt(sum(squared_errors) / len(squared_errors)),
        'correlation': correlation,
    }



def summarize_prediction_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    overall_predictions = [float(item['prediction']) for item in rows]
    overall_targets = [float(item['target']) for item in rows]
    hidden_rows = [item for item in rows if not bool(item['observed'])]
    observed_rows = [item for item in rows if bool(item['observed'])]
    return {
        'row_count': len(rows),
        'hidden_row_count': len(hidden_rows),
        'observed_row_count': len(observed_rows),
        'overall': compute_regression_metrics(overall_predictions, overall_targets),
        'hidden_only': compute_regression_metrics(
            [float(item['prediction']) for item in hidden_rows],
            [float(item['target']) for item in hidden_rows],
        ),
        'observed_only': compute_regression_metrics(
            [float(item['prediction']) for item in observed_rows],
            [float(item['target']) for item in observed_rows],
        ),
    }



def compare_metric_rows(rows: list[dict[str, Any]], metric_path: tuple[str, str] = ('hidden_only', 'mae')) -> list[dict[str, Any]]:
    section_name, metric_name = metric_path
    sorted_rows = sorted(
        rows,
        key=lambda item: (
            float(item.get('metrics', {}).get(section_name, {}).get(metric_name, float('inf'))),
            float(item.get('metrics', {}).get('overall', {}).get('mae', float('inf'))),
            str(item.get('model_type', '')),
        ),
    )
    return sorted_rows
