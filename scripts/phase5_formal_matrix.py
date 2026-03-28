from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _phase4_summary(report_path: Path) -> dict[str, Any]:
    payload = _load_json(report_path)
    comparison = payload.get("comparison", {}) if isinstance(payload.get("comparison"), dict) else {}
    rows = comparison.get("rows") or []
    ranking: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        metrics = item.get("metrics", {}) if isinstance(item.get("metrics"), dict) else {}
        hidden = metrics.get("hidden_only", {}) if isinstance(metrics.get("hidden_only"), dict) else {}
        mae = hidden.get("mae")
        nmae = hidden.get("nmae")
        if not isinstance(mae, (int, float)):
            continue
        ranking.append({
            "model_type": str(item.get("model_type", "")),
            "hidden_mae": float(mae),
            "hidden_nmae": float(nmae) if isinstance(nmae, (int, float)) else None,
        })
    ranking.sort(key=lambda item: item["hidden_mae"])
    best_model = ranking[0]["model_type"] if ranking else None
    best_hidden = ranking[0]["hidden_mae"] if ranking else None
    default_graph_model = str(comparison.get("default_graph_baseline", "gat"))
    default_graph_hidden = None
    for item in ranking:
        if item["model_type"] == default_graph_model:
            default_graph_hidden = item["hidden_mae"]
            break
    return {
        "report_path": str(report_path.resolve()),
        "dataset_name": payload.get("dataset_name"),
        "best_model": best_model,
        "best_hidden_mae": best_hidden,
        "default_graph_model": default_graph_model,
        "default_graph_hidden_mae": default_graph_hidden,
        "ranking_by_hidden_mae": ranking,
    }


def _run_cli(project_root: Path, command: list[str]) -> dict[str, Any]:
    env = os.environ.copy()
    pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = "src" if not pythonpath else f"src:{pythonpath}"
    proc = subprocess.run(
        [sys.executable, "-m", "gic.cli.main", *command],
        cwd=project_root,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"CLI failed: {' '.join(command)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    stdout = proc.stdout.strip()
    if not stdout:
        raise RuntimeError(f"CLI returned empty stdout for {' '.join(command)}")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse CLI JSON for {' '.join(command)}\nSTDOUT:\n{stdout}\nSTDERR:\n{proc.stderr}") from exc
    payload["stderr"] = proc.stderr
    payload["command"] = command
    return payload


def _hidden_metrics(train_payload: dict[str, Any]) -> dict[str, Any]:
    test_metrics = train_payload.get("test_metrics", {})
    hidden = test_metrics.get("hidden_only", {}) if isinstance(test_metrics, dict) else {}
    return {
        "hidden_mae": hidden.get("mae"),
        "hidden_nmae": hidden.get("nmae"),
        "hidden_rmse": hidden.get("rmse"),
        "hidden_correlation": hidden.get("correlation"),
        "hidden_row_count": test_metrics.get("hidden_row_count"),
    }


def _feature_flags(train_payload: dict[str, Any]) -> dict[str, Any]:
    feature_summary = train_payload.get("feature_summary", {})
    signal_summary = train_payload.get("signal_summary", {})
    signal_group = feature_summary.get("global_signal_features", {}) if isinstance(feature_summary, dict) else {}
    return {
        "active_signal_feature_count": signal_group.get("active_count"),
        "dropped_signal_feature_count": signal_group.get("dropped_zero_variance_count"),
        "active_signal_feature_names": signal_group.get("active_names"),
        "signal_quality_flag_counts": signal_summary.get("quality_flag_counts"),
    }


def _run_train(project_root: Path, config_path: Path) -> dict[str, Any]:
    payload = _run_cli(project_root, [
        "train-main-model",
        "--config",
        str(config_path.resolve()),
        "--project-root",
        str(project_root.resolve()),
    ])
    summary = {
        "config_path": str(config_path.resolve()),
        "run_id": payload.get("run_id"),
        "checkpoint_path": payload.get("checkpoint_path"),
        "history_path": payload.get("history_path"),
        "metrics_report_path": payload.get("metrics_report_path"),
        "dataset_path": payload.get("dataset_path"),
        "dataset_summary": payload.get("dataset_summary"),
        "feature_summary": payload.get("feature_summary"),
        "signal_summary": payload.get("signal_summary"),
        **_hidden_metrics(payload),
        **_feature_flags(payload),
    }
    return summary


def _candidate_report(candidate_name: str, broader_result: dict[str, Any], default_result: dict[str, Any] | None, broader_phase4: dict[str, Any], default_phase4: dict[str, Any]) -> dict[str, Any]:
    broader_hidden = broader_result.get("hidden_mae")
    default_hidden = None if default_result is None else default_result.get("hidden_mae")
    beats_broader_graph = isinstance(broader_hidden, (int, float)) and isinstance(broader_phase4.get("default_graph_hidden_mae"), (int, float)) and broader_hidden < broader_phase4["default_graph_hidden_mae"]
    beats_default_graph = None
    if default_result is not None:
        beats_default_graph = isinstance(default_hidden, (int, float)) and isinstance(default_phase4.get("default_graph_hidden_mae"), (int, float)) and default_hidden < default_phase4["default_graph_hidden_mae"]
    dual_closure = bool(beats_broader_graph) and bool(beats_default_graph)
    return {
        "candidate": candidate_name,
        "broader": broader_result,
        "default": default_result,
        "beats_broader_graph": beats_broader_graph,
        "beats_default_graph": beats_default_graph,
        "dual_closure": dual_closure,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default="/home/user/projects/GIC")
    parser.add_argument("--manifest", default="configs/phase5/formal/formal_matrix_manifest.json")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    manifest = _load_json((project_root / args.manifest).resolve())
    broader_candidates = [str(item) for item in manifest.get("broader_candidates", [])]
    fallback_candidates = [str(item) for item in manifest.get("fallback_candidates", [])]

    default_phase4 = _phase4_summary(project_root / 'reports/phase_4_20260327T140729Z_1355128f/phase4_baseline_report.json')
    broader_phase4 = _phase4_summary(project_root / 'reports/phase_4_20260328T022351Z_94f5a566/phase4_baseline_report.json')

    broader_results: dict[str, dict[str, Any]] = {}
    for index, name in enumerate(broader_candidates, start=1):
        print(f'[broader {index}/{len(broader_candidates)}] {name}', file=sys.stderr, flush=True)
        config_path = project_root / 'configs/phase5/formal/broader' / f'{name}.yaml'
        broader_results[name] = _run_train(project_root, config_path)

    ranked = sorted(
        broader_results.items(),
        key=lambda item: float(item[1].get('hidden_mae', float('inf'))),
    )
    top_two = [name for name, _ in ranked[:2]]

    default_results: dict[str, dict[str, Any]] = {}
    candidate_reports: list[dict[str, Any]] = []
    for index, name in enumerate(top_two, start=1):
        print(f'[default replay {index}/{len(top_two)}] {name}', file=sys.stderr, flush=True)
        config_path = project_root / 'configs/phase5/formal/default' / f'{name}.yaml'
        default_results[name] = _run_train(project_root, config_path)
        candidate_reports.append(_candidate_report(name, broader_results[name], default_results[name], broader_phase4, default_phase4))

    if not any(item['dual_closure'] for item in candidate_reports):
        for index, name in enumerate(fallback_candidates, start=1):
            print(f'[fallback broader {index}/{len(fallback_candidates)}] {name}', file=sys.stderr, flush=True)
            config_path = project_root / 'configs/phase5/formal/broader' / f'{name}.yaml'
            broader_results[name] = _run_train(project_root, config_path)
        ranked = sorted(
            broader_results.items(),
            key=lambda item: float(item[1].get('hidden_mae', float('inf'))),
        )
        top_two = [name for name, _ in ranked[:2]]
        candidate_reports = []
        default_results = {}
        for index, name in enumerate(top_two, start=1):
            print(f'[fallback default replay {index}/{len(top_two)}] {name}', file=sys.stderr, flush=True)
            config_path = project_root / 'configs/phase5/formal/default' / f'{name}.yaml'
            default_results[name] = _run_train(project_root, config_path)
            candidate_reports.append(_candidate_report(name, broader_results[name], default_results[name], broader_phase4, default_phase4))

    best_broader_name = ranked[0][0] if ranked else None
    best_default_name = None
    if candidate_reports:
        best_default_name = min(
            candidate_reports,
            key=lambda item: float(item['default']['hidden_mae']) if item['default'] and item['default'].get('hidden_mae') is not None else float('inf'),
        )['candidate']

    payload = {
        'generated_at_utc': _timestamp(),
        'project_root': str(project_root),
        'broader_phase4': broader_phase4,
        'default_phase4': default_phase4,
        'broader_ranked_candidates': [
            {
                'candidate': name,
                **result,
                'beats_broader_graph': (result.get('hidden_mae') is not None and broader_phase4.get('default_graph_hidden_mae') is not None and float(result['hidden_mae']) < float(broader_phase4['default_graph_hidden_mae'])),
                'beats_broader_best': (result.get('hidden_mae') is not None and broader_phase4.get('best_hidden_mae') is not None and float(result['hidden_mae']) < float(broader_phase4['best_hidden_mae'])),
            }
            for name, result in ranked
        ],
        'selected_top_two_for_default': top_two,
        'default_replay_results': candidate_reports,
        'recommended_broader_candidate': best_broader_name,
        'recommended_default_candidate': best_default_name,
        'signal_default_switch_allowed': any(
            item['candidate'].startswith('signal_on') and item['broader']['hidden_mae'] is not None and item['default'] is not None and item['default'].get('hidden_mae') is not None and float(item['broader']['hidden_mae']) < float(broader_results['base_current']['hidden_mae']) and float(item['default']['hidden_mae']) <= float(default_results.get('base_current', item['default']).get('hidden_mae', item['default']['hidden_mae']))
            for item in candidate_reports
        ),
    }
    output_path = Path(args.output).resolve() if args.output else (project_root / 'reports' / f'phase5_formal_matrix_{payload["generated_at_utc"]}.json')
    output_path.write_text(json.dumps(payload, indent=2) + '\n')
    print(json.dumps({'status': 'ok', 'summary_path': str(output_path), 'recommended_broader_candidate': best_broader_name, 'recommended_default_candidate': best_default_name}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
