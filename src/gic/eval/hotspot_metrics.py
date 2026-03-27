from __future__ import annotations

from typing import Any


def compute_hotspot_metrics(probabilities: list[float], targets: list[float], threshold: float = 0.5) -> dict[str, float]:
    if len(probabilities) != len(targets):
        raise ValueError('Hotspot probabilities and targets must have the same length')
    if not probabilities:
        return {
            'accuracy': 0.0,
            'precision': 0.0,
            'recall': 0.0,
            'f1': 0.0,
            'positive_rate': 0.0,
        }
    predicted = [1 if value >= threshold else 0 for value in probabilities]
    truth = [1 if value >= 0.5 else 0 for value in targets]
    tp = sum(1 for pred, target in zip(predicted, truth) if pred == 1 and target == 1)
    fp = sum(1 for pred, target in zip(predicted, truth) if pred == 1 and target == 0)
    fn = sum(1 for pred, target in zip(predicted, truth) if pred == 0 and target == 1)
    tn = sum(1 for pred, target in zip(predicted, truth) if pred == 0 and target == 0)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    accuracy = (tp + tn) / len(predicted)
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'positive_rate': sum(predicted) / len(predicted),
    }



def summarize_hotspot_rows(rows: list[dict[str, Any]], threshold: float = 0.5) -> dict[str, Any]:
    hotspot_rows = [row for row in rows if 'hotspot_target' in row and row.get('hotspot_target') is not None]
    metrics = compute_hotspot_metrics(
        [float(row.get('hotspot_probability', 0.0)) for row in hotspot_rows],
        [float(row.get('hotspot_target', 0.0)) for row in hotspot_rows],
        threshold=threshold,
    )
    return {
        'row_count': len(hotspot_rows),
        'threshold': float(threshold),
        **metrics,
    }
