from __future__ import annotations

from typing import Any


def _hidden_mae(run: dict[str, Any] | None) -> float | None:
    if not run:
        return None
    metrics = dict(run.get("metrics", {}))
    hidden_only = dict(metrics.get("hidden_only", {}))
    overall = dict(metrics.get("overall", {}))
    if int(metrics.get("hidden_row_count", 0)) > 0:
        return float(hidden_only.get("mae", 0.0))
    if overall:
        return float(overall.get("mae", 0.0))
    return None


def _best_run_kg_summary(ablation_payload: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(ablation_payload, dict):
        return {}
    best_run = ablation_payload.get("best_run")
    if not isinstance(best_run, dict):
        return {}
    return dict(best_run.get("kg_summary", {}))


def build_kg_report_payload(
    *,
    dataset_name: str,
    dataset_path: str,
    manifest: dict[str, Any],
    validation: dict[str, Any],
    feature_payload: dict[str, Any],
    rule_payload: dict[str, Any],
    query_examples: list[dict[str, Any]],
    phase5_report_path: str | None,
    ablation_payload: dict[str, Any] | None = None,
    surface_results: dict[str, Any] | None = None,
    default_promotion_decision: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "dataset_name": dataset_name,
        "dataset_path": dataset_path,
        "manifest": manifest,
        "validation": validation,
        "feature_summary": {
            "graph_count": int(feature_payload.get("graph_count", 0)),
            "global_feature_count": len(feature_payload.get("global_feature_names", [])),
            "node_feature_count": len(feature_payload.get("node_feature_names", [])),
        },
        "feature_group_summary": dict(feature_payload.get("feature_groups", {})),
        "rule_summary": {
            "graph_count": int(rule_payload.get("graph_count", 0)),
            "rule_counts": dict(rule_payload.get("rule_counts", {})),
        },
        "query_examples": query_examples,
        "phase5_control_report_path": phase5_report_path,
    }
    if isinstance(ablation_payload, dict):
        no_kg_run = ablation_payload.get("no_kg_run")
        best_run = ablation_payload.get("best_run")
        payload["model_comparison"] = {
            "compare_split": ablation_payload.get("compare_split", "test"),
            "phase5_control": ablation_payload.get("phase5_control"),
            "recommended_variant": ablation_payload.get("recommended_variant"),
            "best_variant": best_run.get("variant_name") if isinstance(best_run, dict) else None,
            "best_hidden_mae": _hidden_mae(best_run),
            "no_kg_hidden_mae": _hidden_mae(no_kg_run),
            "kg_beats_no_kg": (
                _hidden_mae(best_run) is not None
                and _hidden_mae(no_kg_run) is not None
                and float(_hidden_mae(best_run)) < float(_hidden_mae(no_kg_run))
            ),
            "ablations": [
                {
                    "variant_name": row.get("variant_name"),
                    "hidden_mae": row.get("hidden_mae"),
                    "overall_mae": row.get("overall_mae"),
                    "kg_enabled": row.get("kg_enabled"),
                    "kg_rule_feature_count": row.get("kg_rule_feature_count", 0),
                    "relation_feature_count": row.get("relation_feature_count", 0),
                }
                for row in ablation_payload.get("ablations", [])
            ],
        }
    kg_summary = _best_run_kg_summary(ablation_payload)
    payload["relation_light_summary"] = {
        "configured_use_relation_light": bool(kg_summary.get("configured_use_relation_light", False)),
        "active_relation_global_feature_count": int(kg_summary.get("active_relation_global_feature_count", 0)),
        "active_relation_node_feature_count": int(kg_summary.get("active_relation_node_feature_count", 0)),
        "active_relation_global_feature_names": list(kg_summary.get("active_relation_global_feature_names", [])),
        "active_relation_node_feature_names": list(kg_summary.get("active_relation_node_feature_names", [])),
    }
    payload["rule_variance_summary"] = dict(kg_summary.get("rule_variance_summary", {}))
    payload["active_feature_group_summary"] = dict(kg_summary.get("feature_group_summary", {}))
    if isinstance(surface_results, dict) and surface_results:
        payload["surface_results"] = surface_results
    if isinstance(default_promotion_decision, dict) and default_promotion_decision:
        payload["default_promotion_decision"] = default_promotion_decision
    elif isinstance(surface_results, dict) and surface_results:
        payload["default_promotion_decision"] = {
            "primary_surface": dataset_name,
            "summary": "report_only",
        }
    return payload


def build_kg_report_markdown(payload: dict[str, Any]) -> str:
    manifest = payload["manifest"]
    feature_summary = payload["feature_summary"]
    rule_summary = payload["rule_summary"]
    lines = [
        "# Phase 6 KG Report",
        "",
        f"- dataset: `{payload['dataset_name']}`",
        f"- entity count: `{manifest['entity_count']}`",
        f"- relation count: `{manifest['relation_count']}`",
        f"- global feature count: `{feature_summary['global_feature_count']}`",
        f"- node feature count: `{feature_summary['node_feature_count']}`",
        f"- rule graph count: `{rule_summary['graph_count']}`",
        f"- phase5 control report: `{payload['phase5_control_report_path'] or ''}`",
        "",
        "## Entity Types",
    ]
    for key, value in sorted(payload["validation"]["entity_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Relation Types"])
    for key, value in sorted(payload["validation"]["relation_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Rule Counts"])
    for key, value in sorted(rule_summary["rule_counts"].items()):
        lines.append(f"- `{key}`: `{value}`")

    model_comparison = payload.get("model_comparison")
    if isinstance(model_comparison, dict):
        lines.extend(["", "## Model Comparison"])
        lines.append(f"- compare split: `{model_comparison.get('compare_split', '')}`")
        lines.append(f"- recommended variant: `{model_comparison.get('recommended_variant', '')}`")
        lines.append(f"- best variant: `{model_comparison.get('best_variant', '')}`")
        lines.append(f"- best hidden MAE: `{model_comparison.get('best_hidden_mae', '')}`")
        lines.append(f"- no KG hidden MAE: `{model_comparison.get('no_kg_hidden_mae', '')}`")
        lines.append(f"- KG beats no KG: `{model_comparison.get('kg_beats_no_kg', False)}`")
        phase5_control = model_comparison.get("phase5_control")
        if isinstance(phase5_control, dict):
            lines.append(f"- frozen phase5 hidden MAE: `{phase5_control.get('hidden_mae', '')}`")
        lines.extend(["", "## KG Ablations"])
        for row in model_comparison.get("ablations", []):
            lines.append(
                f"- `{row['variant_name']}`: hidden MAE `{row['hidden_mae']}`, overall MAE `{row['overall_mae']}`, "
                f"kg enabled `{row['kg_enabled']}`, rule features `{row['kg_rule_feature_count']}`, relation features `{row['relation_feature_count']}`"
            )

    surface_results = payload.get("surface_results")
    if isinstance(surface_results, dict) and surface_results:
        lines.extend(["", "## Multi-Surface Summary"])
        for variant_name, variant_payload in sorted(surface_results.items()):
            lines.append(f"- variant `{variant_name}`")
            for surface_name, surface_metrics in sorted(dict(variant_payload).items()):
                lines.append(
                    f"- surface `{surface_name}`: hidden MAE `{surface_metrics.get('hidden_mae', '')}`, overall MAE `{surface_metrics.get('overall_mae', '')}`"
                )

    feature_group_summary = payload.get("active_feature_group_summary")
    if isinstance(feature_group_summary, dict) and feature_group_summary:
        lines.extend(["", "## Active Feature Groups"])
        for level_name, groups in sorted(feature_group_summary.items()):
            lines.append(f"- `{level_name}`")
            if isinstance(groups, dict):
                for group_name, names in sorted(groups.items()):
                    lines.append(f"- {level_name}.{group_name}: `{len(list(names))}` active")

    relation_summary = payload.get("relation_light_summary")
    if isinstance(relation_summary, dict):
        lines.extend(["", "## Relation-Light Summary"])
        lines.append(f"- configured: `{relation_summary.get('configured_use_relation_light', False)}`")
        lines.append(f"- active relation global feature count: `{relation_summary.get('active_relation_global_feature_count', 0)}`")
        lines.append(f"- active relation node feature count: `{relation_summary.get('active_relation_node_feature_count', 0)}`")

    rule_variance_summary = payload.get("rule_variance_summary")
    if isinstance(rule_variance_summary, dict):
        lines.extend(["", "## Rule Variance Summary"])
        lines.append(f"- active rule features: `{len(rule_variance_summary.get('active_rule_features', []))}`")
        lines.append(f"- dropped rule features: `{len(rule_variance_summary.get('dropped_rule_features', []))}`")

    decision = payload.get("default_promotion_decision")
    if isinstance(decision, dict):
        lines.extend(["", "## Default Promotion Decision"])
        for key, value in decision.items():
            lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Query Examples"])
    for example in payload["query_examples"]:
        lines.append(
            f"- `{example['graph_id']}` -> scenario `{example['scenario_id']}` with `{len(example['rule_findings'])}` rule findings"
        )
    return "\n".join(lines)
