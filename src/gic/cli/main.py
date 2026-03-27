from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

from gic.config import dump_config, load_config
from gic.data import RegistryStore, to_dict
from gic.data.converters.grid_to_physics import convert_grid_case_to_physics
from gic.data.loaders.matpower_loader import MatpowerLoader
from gic.data.loaders.timeseries_loader import TimeSeriesLoader
from gic.data.validation.checks import (
    validate_geomagnetic_timeseries,
    validate_grid_case,
    validate_registry_consistency,
)
from gic.data.validation.reports import summarize_validation_results, write_validation_report
from gic.physics.export import export_label_bundle
from gic.physics.field import build_series_from_timeseries, uniform_field_from_scenario
from gic.physics.postprocess import summarize_solution
from gic.physics.scenarios import generate_scenarios
from gic.physics.solver import solve_series, solve_snapshot
from gic.physics.validation import validate_physics_case, validate_solution
from gic.signal import (
    FrontendConfig,
    build_comparison_report,
    build_frontend,
    build_signal_sample_from_timeseries,
    export_comparison_report,
    export_frontend_result,
    signal_to_dict,
    validate_frontend_result,
    validate_signal_sample,
)
from gic.utils.logging_utils import configure_logger
from gic.utils.paths import ensure_directory, resolve_project_root
from gic.utils.runtime import initialize_run, write_summary

DEFAULT_CONFIG = "configs/phase0/phase0_dev.yaml"
DEFAULT_PHASE1_CONFIG = "configs/phase1/phase1_dev.yaml"
DEFAULT_PHASE2_CONFIG = "configs/phase2/phase2_dev.yaml"
DEFAULT_PHASE3_CONFIG = "configs/phase3/phase3_dev.yaml"


def _common_run_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to the config file")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override for writing artifacts, logs, reports, and data outputs",
    )


def _common_data_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_PHASE1_CONFIG, help="Path to the Phase 1 config file")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override for registry and output resolution",
    )
    parser.add_argument("--dataset-name", default=None, help="Optional dataset name override")


def _common_physics_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_PHASE2_CONFIG, help="Path to the Phase 2 config file")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override for registry, processed outputs, and reports",
    )
    parser.add_argument("--scenario-mode", default=None, help="Optional scenario mode override")


def _common_signal_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_PHASE3_CONFIG, help="Path to the Phase 3 config file")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override for registry, processed outputs, and reports",
    )
    parser.add_argument("--dataset-name", default=None, help="Optional Phase 3 dataset override")
    parser.add_argument("--method", default=None, help="Optional frontend method override")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gic")
    subparsers = parser.add_subparsers(dest="command", required=True)

    show_config = subparsers.add_parser("show-config", help="Print the resolved configuration")
    show_config.add_argument("--config", default=DEFAULT_CONFIG, help="Path to the config file")
    show_config.set_defaults(func=cmd_show_config)

    init_run = subparsers.add_parser("init-run", help="Create run directories and metadata")
    _common_run_parser(init_run)
    init_run.set_defaults(func=cmd_init_run)

    run_cmd = subparsers.add_parser("run", help="Execute the Phase 0 dry run")
    _common_run_parser(run_cmd)
    run_cmd.set_defaults(func=cmd_run)

    validate_env = subparsers.add_parser("validate-env", help="Print a lightweight env summary")
    validate_env.set_defaults(func=cmd_validate_env)

    data_list_sources = subparsers.add_parser("data-list-sources", help="List registered data sources")
    _common_data_parser(data_list_sources)
    data_list_sources.set_defaults(func=cmd_data_list_sources)

    data_list_datasets = subparsers.add_parser("data-list-datasets", help="List registered datasets")
    _common_data_parser(data_list_datasets)
    data_list_datasets.set_defaults(func=cmd_data_list_datasets)

    data_validate = subparsers.add_parser("data-validate", help="Validate registry and active datasets")
    _common_data_parser(data_validate)
    data_validate.set_defaults(func=cmd_data_validate)

    data_build_manifest = subparsers.add_parser("data-build-manifest", help="Build a manifest for a dataset")
    _common_data_parser(data_build_manifest)
    data_build_manifest.set_defaults(func=cmd_data_build_manifest)

    data_convert_sample = subparsers.add_parser("data-convert-sample", help="Convert active sample datasets")
    _common_data_parser(data_convert_sample)
    data_convert_sample.set_defaults(func=cmd_data_convert_sample)

    physics_build_case = subparsers.add_parser("physics-build-case", help="Build a PhysicsGridCase from a GridCase")
    _common_physics_parser(physics_build_case)
    physics_build_case.set_defaults(func=cmd_physics_build_case)

    physics_solve_snapshot = subparsers.add_parser("physics-solve-snapshot", help="Solve a single uniform field snapshot")
    _common_physics_parser(physics_solve_snapshot)
    physics_solve_snapshot.set_defaults(func=cmd_physics_solve_snapshot)

    physics_solve_series = subparsers.add_parser("physics-solve-series", help="Solve a time-series field scenario")
    _common_physics_parser(physics_solve_series)
    physics_solve_series.set_defaults(func=cmd_physics_solve_series)

    physics_generate_scenarios = subparsers.add_parser("physics-generate-scenarios", help="Generate scenario metadata")
    _common_physics_parser(physics_generate_scenarios)
    physics_generate_scenarios.set_defaults(func=cmd_physics_generate_scenarios)

    physics_export_labels = subparsers.add_parser("physics-export-labels", help="Export labels for configured physics scenarios")
    _common_physics_parser(physics_export_labels)
    physics_export_labels.set_defaults(func=cmd_physics_export_labels)

    physics_validate_solution = subparsers.add_parser("physics-validate-solution", help="Run physics sanity checks")
    _common_physics_parser(physics_validate_solution)
    physics_validate_solution.set_defaults(func=cmd_physics_validate_solution)

    signal_run_frontend = subparsers.add_parser("signal-run-frontend", help="Run one Phase 3 frontend method")
    _common_signal_parser(signal_run_frontend)
    signal_run_frontend.set_defaults(func=cmd_signal_run_frontend)

    signal_compare_frontends = subparsers.add_parser("signal-compare-frontends", help="Compare active Phase 3 frontend methods")
    _common_signal_parser(signal_compare_frontends)
    signal_compare_frontends.set_defaults(func=cmd_signal_compare_frontends)

    signal_export_features = subparsers.add_parser("signal-export-features", help="Export signal-ready assets for Phase 3 methods")
    _common_signal_parser(signal_export_features)
    signal_export_features.set_defaults(func=cmd_signal_export_features)

    signal_validate_input = subparsers.add_parser("signal-validate-input", help="Validate Phase 3 signal input preparation")
    _common_signal_parser(signal_validate_input)
    signal_validate_input.set_defaults(func=cmd_signal_validate_input)

    signal_build_report = subparsers.add_parser("signal-build-report", help="Build a Phase 3 comparison report")
    _common_signal_parser(signal_build_report)
    signal_build_report.set_defaults(func=cmd_signal_build_report)

    return parser


def _serialize_result(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def _load_phase1_context(args: argparse.Namespace) -> tuple[dict[str, Any], Path, RegistryStore]:
    config = load_config(args.config)
    project_root = resolve_project_root(args.project_root)
    data_cfg = config.get("data")
    if not isinstance(data_cfg, dict):
        raise ValueError("Phase 1 config requires a data section")
    registry_root = data_cfg.get("registry_root")
    if not isinstance(registry_root, str) or not registry_root:
        raise ValueError("Phase 1 config requires data.registry_root")
    registry = RegistryStore(project_root=project_root, registry_root=registry_root)
    return config, project_root, registry


def _load_phase2_context(args: argparse.Namespace) -> tuple[dict[str, Any], Path, RegistryStore]:
    config = load_config(args.config)
    project_root = resolve_project_root(args.project_root)
    data_cfg = config.get("data")
    if not isinstance(data_cfg, dict):
        raise ValueError("Phase 2 config requires a data section")
    registry_root = data_cfg.get("registry_root")
    if not isinstance(registry_root, str) or not registry_root:
        raise ValueError("Phase 2 config requires data.registry_root")
    registry = RegistryStore(project_root=project_root, registry_root=registry_root)
    return config, project_root, registry


def _load_phase3_context(args: argparse.Namespace) -> tuple[dict[str, Any], Path, RegistryStore]:
    config = load_config(args.config)
    project_root = resolve_project_root(args.project_root)
    data_cfg = config.get("data")
    if not isinstance(data_cfg, dict):
        raise ValueError("Phase 3 config requires a data section")
    registry_root = data_cfg.get("registry_root")
    if not isinstance(registry_root, str) or not registry_root:
        raise ValueError("Phase 3 config requires data.registry_root")
    registry = RegistryStore(project_root=project_root, registry_root=registry_root)
    return config, project_root, registry


def _convert_dataset(
    *,
    project_root: Path,
    config: dict[str, Any],
    registry: RegistryStore,
    dataset_name: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    dataset = registry.get_dataset(dataset_name)
    source = registry.get_source(dataset.source_name)
    interim_root = project_root / config["data"]["interim_root"]
    if source.source_type == "grid_case":
        asset, manifest = MatpowerLoader(project_root).load(dataset, source)
        output_dir = ensure_directory(interim_root / "grid_cases")
        output_path = output_dir / f"{dataset.dataset_name}.json"
    elif source.source_type == "geomagnetic_timeseries":
        asset, manifest = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
        output_dir = ensure_directory(interim_root / "timeseries")
        output_path = output_dir / f"{dataset.dataset_name}.json"
    else:
        raise ValueError(f"Unsupported source type for conversion: {source.source_type}")

    output_path.write_text(json.dumps(to_dict(asset), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest_path = output_dir / f"{dataset.dataset_name}.manifest.json"
    if config["data"]["conversion"].get("write_manifest", True):
        manifest_path.write_text(json.dumps(to_dict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    payload = {
        "dataset_name": dataset.dataset_name,
        "source_name": source.source_name,
        "source_type": source.source_type,
        "output_path": str(output_path),
        "manifest_path": str(manifest_path),
    }
    return payload, to_dict(manifest)


def _validate_active_assets(project_root: Path, registry: RegistryStore) -> list[dict[str, Any]]:
    results = [validate_registry_consistency(registry)]
    for dataset in registry.active_datasets():
        source = registry.get_source(dataset.source_name)
        if source.source_type == "grid_case":
            asset, _ = MatpowerLoader(project_root).load(dataset, source)
            results.append(validate_grid_case(asset))
        elif source.source_type == "geomagnetic_timeseries":
            asset, _ = TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)
            results.append(validate_geomagnetic_timeseries(asset))
    return results


def _load_grid_case_from_registry(project_root: Path, registry: RegistryStore, dataset_name: str):
    dataset = registry.get_dataset(dataset_name)
    source = registry.get_source(dataset.source_name)
    return MatpowerLoader(project_root).load(dataset, source)


def _load_geomagnetic_series_from_registry(project_root: Path, registry: RegistryStore, dataset_name: str):
    dataset = registry.get_dataset(dataset_name)
    source = registry.get_source(dataset.source_name)
    return TimeSeriesLoader(project_root).load_geomagnetic(dataset, source)


def _solve_physics_mode(
    *,
    config: dict[str, Any],
    project_root: Path,
    registry: RegistryStore,
    scenario_mode: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    scenarios = generate_scenarios(config, scenario_mode)
    outputs: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    for scenario in scenarios:
        grid_case, _ = _load_grid_case_from_registry(project_root, registry, scenario.case_dataset)
        physics_case = convert_grid_case_to_physics(grid_case, config["physics"])
        physics_case_report = validate_physics_case(physics_case)

        if scenario.scenario_type == "timeseries_field":
            if not scenario.timeseries_dataset:
                raise ValueError("timeseries_field scenario requires timeseries_dataset")
            series, _ = _load_geomagnetic_series_from_registry(project_root, registry, scenario.timeseries_dataset)
            field_series = build_series_from_timeseries(
                scenario,
                series,
                float(config["physics"]["field"].get("geomagnetic_scale_v_per_km_per_nt", 0.01)),
            )
            solutions = solve_series(physics_case, field_series, scenario.scenario_id)
        else:
            snapshot = uniform_field_from_scenario(scenario)
            solutions = [solve_snapshot(physics_case, snapshot, scenario.scenario_id)]

        solution_reports = [validate_solution(item) for item in solutions]
        exported_paths = export_label_bundle(
            project_root=project_root,
            outputs_config=config["physics"]["outputs"],
            scenario=scenario,
            solutions=solutions,
        )
        outputs.append(
            {
                "scenario_id": scenario.scenario_id,
                "scenario_type": scenario.scenario_type,
                "solution_count": len(solutions),
                "exported_paths": exported_paths,
                "solution_summaries": [summarize_solution(item) for item in solutions],
            }
        )
        reports.append(
            {
                "scenario_id": scenario.scenario_id,
                "physics_case": physics_case_report,
                "solutions": solution_reports,
            }
        )
    return outputs, reports


def _phase3_dataset_name(args: argparse.Namespace, config: dict[str, Any]) -> str:
    signal_cfg = config.get("signal")
    if not isinstance(signal_cfg, dict):
        raise ValueError("Phase 3 config requires a signal section")
    dataset_name = args.dataset_name or signal_cfg.get("input_dataset")
    if not isinstance(dataset_name, str) or not dataset_name:
        raise ValueError("Phase 3 requires signal.input_dataset or --dataset-name")
    return dataset_name


def _build_phase3_frontend_config(config: dict[str, Any], method_name: str) -> FrontendConfig:
    signal_cfg = config.get("signal")
    if not isinstance(signal_cfg, dict):
        raise ValueError("Phase 3 config requires a signal section")
    methods_cfg = signal_cfg.get("methods")
    if not isinstance(methods_cfg, dict) or method_name not in methods_cfg:
        raise ValueError(f"Phase 3 config missing method configuration for {method_name}")
    method_cfg = methods_cfg[method_name]
    if not isinstance(method_cfg, dict):
        raise ValueError(f"Method config must be a mapping: {method_name}")
    parameters = method_cfg.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError(f"Method parameters must be a mapping: {method_name}")
    return FrontendConfig(
        method_name=method_name,
        method_version=str(method_cfg.get("method_version", "1.0")),
        parameters=dict(parameters),
    )


def _phase3_active_methods(args: argparse.Namespace, config: dict[str, Any]) -> list[str]:
    if args.method:
        return [args.method]
    signal_cfg = config.get("signal")
    if not isinstance(signal_cfg, dict):
        raise ValueError("Phase 3 config requires a signal section")
    comparison_cfg = signal_cfg.get("comparison", {})
    if not isinstance(comparison_cfg, dict):
        comparison_cfg = {}
    active_methods = comparison_cfg.get("active_methods")
    if not isinstance(active_methods, list) or not active_methods:
        raise ValueError("Phase 3 config requires signal.comparison.active_methods")
    return [str(item) for item in active_methods]


def _phase3_signal_sample(
    *,
    config: dict[str, Any],
    project_root: Path,
    registry: RegistryStore,
    dataset_name: str,
):
    signal_cfg = config.get("signal")
    if not isinstance(signal_cfg, dict):
        raise ValueError("Phase 3 config requires a signal section")
    series, _ = _load_geomagnetic_series_from_registry(project_root, registry, dataset_name)
    return build_signal_sample_from_timeseries(series, signal_cfg)


def _run_phase3_methods(
    *,
    config: dict[str, Any],
    project_root: Path,
    registry: RegistryStore,
    dataset_name: str,
    method_names: list[str],
    export_results: bool,
    build_report: bool,
) -> dict[str, Any]:
    signal_cfg = config["signal"]
    sample = _phase3_signal_sample(
        config=config,
        project_root=project_root,
        registry=registry,
        dataset_name=dataset_name,
    )
    sample_validation = validate_signal_sample(sample)
    results = []
    exports = []
    validations = [sample_validation]
    if sample_validation["ok"]:
        for method_name in method_names:
            frontend = build_frontend(method_name)
            frontend_config = _build_phase3_frontend_config(config, method_name)
            result = frontend.run(sample, frontend_config)
            result_validation = validate_frontend_result(result)
            validations.append(result_validation)
            results.append(result)
            if export_results:
                exports.append(
                    {
                        "method_name": method_name,
                        "paths": export_frontend_result(
                            project_root=project_root,
                            signal_config=signal_cfg,
                            signal_sample=sample,
                            result=result,
                        ),
                    }
                )

    comparison_report = None
    comparison_path = None
    if build_report and results:
        comparison_report = build_comparison_report(
            sample_id=sample.sample_id,
            results=results,
            comparison_config=signal_cfg.get("comparison", {}),
        )
        if signal_cfg.get("comparison", {}).get("export_report", True):
            comparison_path = export_comparison_report(
                project_root=project_root,
                signal_config=signal_cfg,
                comparison_report=comparison_report,
            )

    return {
        "sample": sample,
        "sample_validation": sample_validation,
        "results": results,
        "exports": exports,
        "validations": validations,
        "comparison_report": comparison_report,
        "comparison_path": comparison_path,
    }


def cmd_show_config(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    print(dump_config(config))
    return 0


def cmd_init_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    context, metadata = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="init-run",
        project_root=args.project_root,
    )
    _serialize_result(
        {
            "config_path": metadata["config_path"],
            "log_file": str(context.log_file),
            "metadata_path": str(context.metadata_path),
            "run_id": context.run_id,
            "summary_path": str(context.summary_path),
        }
    )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    context, metadata = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="run",
        project_root=args.project_root,
    )
    logger = configure_logger("gic.phase0", config["logging"]["level"], context.log_file)
    logger.info("Starting Phase 0 dry run")
    logger.info("Loaded config from %s", metadata["config_path"])
    logger.info("Run ID: %s", context.run_id)

    summary = {
        "status": "ok",
        "stage": config["project"]["stage"],
        "profile": config["project"].get("profile", "default"),
        "mode": config["runtime"]["mode"],
        "run_id": context.run_id,
    }
    write_summary(context, summary)
    logger.info("Wrote summary to %s", context.summary_path)
    logger.info("Phase 0 dry run completed")

    _serialize_result(
        {
            "artifact_dir": str(context.artifact_dir),
            "log_file": str(context.log_file),
            "run_id": context.run_id,
            "summary_path": str(context.summary_path),
        }
    )
    return 0


def cmd_validate_env(_: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "conda_env": os.environ.get("CONDA_DEFAULT_ENV", ""),
        "cwd": str(Path.cwd().resolve()),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "wsl_distro": os.environ.get("WSL_DISTRO_NAME", ""),
    }
    try:
        import torch  # type: ignore

        payload["torch"] = {
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count(),
        }
        if torch.cuda.is_available() and torch.cuda.device_count() > 0:
            payload["torch"]["cuda_device_0"] = torch.cuda.get_device_name(0)
    except Exception as exc:  # pragma: no cover
        payload["torch"] = {"error": f"{type(exc).__name__}: {exc}"}
    _serialize_result(payload)
    return 0


def cmd_data_list_sources(args: argparse.Namespace) -> int:
    _, _, registry = _load_phase1_context(args)
    _serialize_result({"sources": [to_dict(item) for item in registry.list_sources()]})
    return 0


def cmd_data_list_datasets(args: argparse.Namespace) -> int:
    _, _, registry = _load_phase1_context(args)
    _serialize_result({"datasets": [to_dict(item) for item in registry.list_datasets()]})
    return 0


def cmd_data_validate(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase1_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="data-validate",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase1.validate", config["logging"]["level"], context.log_file)
    logger.info("Starting Phase 1 data validation")
    results = _validate_active_assets(project_root, registry)
    summary = summarize_validation_results(results)
    report_path = write_validation_report(summary, context.report_dir / "data_validation_report.json")
    write_summary(
        context,
        {
            "status": "ok" if summary["error_count"] == 0 else "failed",
            "run_id": context.run_id,
            "report_path": str(report_path),
            "result_count": summary["result_count"],
            "error_count": summary["error_count"],
            "warning_count": summary["warning_count"],
        },
    )
    logger.info("Validation report written to %s", report_path)
    _serialize_result(
        {
            "run_id": context.run_id,
            "report_path": str(report_path),
            "summary": summary,
        }
    )
    return 0 if summary["error_count"] == 0 else 1


def cmd_data_build_manifest(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase1_context(args)
    dataset_name = args.dataset_name
    if not dataset_name:
        raise ValueError("data-build-manifest requires --dataset-name")
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="data-build-manifest",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase1.manifest", config["logging"]["level"], context.log_file)
    payload, manifest = _convert_dataset(
        project_root=project_root,
        config=config,
        registry=registry,
        dataset_name=dataset_name,
    )
    write_summary(context, {"status": "ok", "dataset_name": dataset_name, "manifest": manifest})
    logger.info("Built manifest for dataset %s", dataset_name)
    _serialize_result(payload)
    return 0


def cmd_data_convert_sample(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase1_context(args)
    dataset_names = [args.dataset_name] if args.dataset_name else [item.dataset_name for item in registry.active_datasets()]
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="data-convert-sample",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase1.convert", config["logging"]["level"], context.log_file)
    outputs = []
    manifests = []
    for dataset_name in dataset_names:
        payload, manifest = _convert_dataset(
            project_root=project_root,
            config=config,
            registry=registry,
            dataset_name=dataset_name,
        )
        outputs.append(payload)
        manifests.append(manifest)
        logger.info("Converted dataset %s -> %s", dataset_name, payload["output_path"])
    write_summary(context, {"status": "ok", "datasets": dataset_names, "outputs": outputs})
    _serialize_result({"run_id": context.run_id, "outputs": outputs, "manifest_count": len(manifests)})
    return 0


def cmd_physics_build_case(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase2_context(args)
    scenario_cfg = config["scenario"]
    grid_case, _ = _load_grid_case_from_registry(project_root, registry, scenario_cfg["case_dataset"])
    physics_case = convert_grid_case_to_physics(grid_case, config["physics"])
    outputs_root = ensure_directory(project_root / config["physics"]["outputs"]["physics_ready_root"])
    destination = outputs_root / f"{physics_case.case_id}.json"
    destination.write_text(json.dumps(to_dict(physics_case), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _serialize_result({"case_id": physics_case.case_id, "output_path": str(destination)})
    return 0


def cmd_physics_solve_snapshot(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase2_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="physics-solve-snapshot",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase2.snapshot", config["logging"]["level"], context.log_file)
    outputs, reports = _solve_physics_mode(
        config=config,
        project_root=project_root,
        registry=registry,
        scenario_mode="uniform_field",
    )
    write_summary(context, {"status": "ok", "outputs": outputs, "reports": reports})
    logger.info("Completed uniform snapshot physics solve")
    _serialize_result({"run_id": context.run_id, "outputs": outputs, "reports": reports})
    return 0


def cmd_physics_solve_series(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase2_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="physics-solve-series",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase2.series", config["logging"]["level"], context.log_file)
    outputs, reports = _solve_physics_mode(
        config=config,
        project_root=project_root,
        registry=registry,
        scenario_mode="timeseries_field",
    )
    write_summary(context, {"status": "ok", "outputs": outputs, "reports": reports})
    logger.info("Completed time-series physics solve")
    _serialize_result({"run_id": context.run_id, "outputs": outputs, "reports": reports})
    return 0


def cmd_physics_generate_scenarios(args: argparse.Namespace) -> int:
    config, project_root, _ = _load_phase2_context(args)
    scenario_mode = args.scenario_mode or config["scenario"].get("type", "uniform_field")
    scenarios = generate_scenarios(config, scenario_mode)
    datasets_root = ensure_directory(project_root / config["physics"]["outputs"]["datasets_root"])
    destination = datasets_root / f"generated_{scenario_mode}_scenarios.json"
    destination.write_text(json.dumps([to_dict(item) for item in scenarios], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _serialize_result({"scenario_count": len(scenarios), "output_path": str(destination)})
    return 0


def cmd_physics_export_labels(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase2_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="physics-export-labels",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase2.export", config["logging"]["level"], context.log_file)
    scenario_mode = args.scenario_mode or config["scenario"].get("type", "uniform_field")
    outputs, reports = _solve_physics_mode(
        config=config,
        project_root=project_root,
        registry=registry,
        scenario_mode=scenario_mode,
    )
    write_summary(context, {"status": "ok", "outputs": outputs, "reports": reports})
    logger.info("Exported physics labels for scenario mode %s", scenario_mode)
    _serialize_result({"run_id": context.run_id, "outputs": outputs, "reports": reports})
    return 0


def cmd_physics_validate_solution(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase2_context(args)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="physics-validate-solution",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase2.validate", config["logging"]["level"], context.log_file)
    outputs, reports = _solve_physics_mode(
        config=config,
        project_root=project_root,
        registry=registry,
        scenario_mode="uniform_field",
    )
    summary = summarize_validation_results([reports[0]["physics_case"], *reports[0]["solutions"]])
    report_path = write_validation_report(summary, context.report_dir / "physics_validation_report.json")
    write_summary(context, {"status": "ok", "report_path": str(report_path), "outputs": outputs})
    logger.info("Physics validation report written to %s", report_path)
    _serialize_result({"run_id": context.run_id, "report_path": str(report_path), "summary": summary})
    return 0


def cmd_signal_validate_input(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase3_context(args)
    dataset_name = _phase3_dataset_name(args, config)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="signal-validate-input",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase3.validate", config["logging"]["level"], context.log_file)
    sample = _phase3_signal_sample(config=config, project_root=project_root, registry=registry, dataset_name=dataset_name)
    sample_validation = validate_signal_sample(sample)
    summary = summarize_validation_results([sample_validation])
    report_path = write_validation_report(summary, context.report_dir / "signal_validation_report.json")
    write_summary(context, {"status": "ok" if sample_validation["ok"] else "failed", "dataset_name": dataset_name, "report_path": str(report_path)})
    logger.info("Signal input validation report written to %s", report_path)
    _serialize_result({
        "run_id": context.run_id,
        "dataset_name": dataset_name,
        "sample_id": sample.sample_id,
        "report_path": str(report_path),
        "summary": summary,
    })
    return 0 if sample_validation["ok"] else 1


def cmd_signal_run_frontend(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase3_context(args)
    dataset_name = _phase3_dataset_name(args, config)
    method_names = _phase3_active_methods(args, config)[:1]
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="signal-run-frontend",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase3.run", config["logging"]["level"], context.log_file)
    payload = _run_phase3_methods(
        config=config,
        project_root=project_root,
        registry=registry,
        dataset_name=dataset_name,
        method_names=method_names,
        export_results=True,
        build_report=False,
    )
    summary = summarize_validation_results(payload["validations"])
    write_summary(
        context,
        {
            "status": "ok" if summary["error_count"] == 0 else "failed",
            "dataset_name": dataset_name,
            "methods": method_names,
            "exports": payload["exports"],
        },
    )
    logger.info("Completed signal frontend run for %s", method_names[0])
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_name": dataset_name,
            "sample_id": payload["sample"].sample_id,
            "methods": method_names,
            "exports": payload["exports"],
            "validation_summary": summary,
            "result": signal_to_dict(payload["results"][0]) if payload["results"] else None,
        }
    )
    return 0 if summary["error_count"] == 0 else 1


def cmd_signal_compare_frontends(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase3_context(args)
    dataset_name = _phase3_dataset_name(args, config)
    method_names = _phase3_active_methods(args, config)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="signal-compare-frontends",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase3.compare", config["logging"]["level"], context.log_file)
    payload = _run_phase3_methods(
        config=config,
        project_root=project_root,
        registry=registry,
        dataset_name=dataset_name,
        method_names=method_names,
        export_results=True,
        build_report=True,
    )
    summary = summarize_validation_results(payload["validations"])
    comparison_report = payload["comparison_report"]
    write_summary(
        context,
        {
            "status": "ok" if summary["error_count"] == 0 else "failed",
            "dataset_name": dataset_name,
            "default_method": comparison_report.default_method if comparison_report else None,
            "comparison_path": payload["comparison_path"],
        },
    )
    logger.info("Completed signal frontend comparison across %d methods", len(method_names))
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_name": dataset_name,
            "sample_id": payload["sample"].sample_id,
            "methods": method_names,
            "exports": payload["exports"],
            "comparison_path": payload["comparison_path"],
            "comparison_report": signal_to_dict(comparison_report) if comparison_report else None,
            "validation_summary": summary,
        }
    )
    return 0 if summary["error_count"] == 0 else 1


def cmd_signal_export_features(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase3_context(args)
    dataset_name = _phase3_dataset_name(args, config)
    method_names = _phase3_active_methods(args, config)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="signal-export-features",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase3.export", config["logging"]["level"], context.log_file)
    payload = _run_phase3_methods(
        config=config,
        project_root=project_root,
        registry=registry,
        dataset_name=dataset_name,
        method_names=method_names,
        export_results=True,
        build_report=False,
    )
    summary = summarize_validation_results(payload["validations"])
    write_summary(context, {"status": "ok" if summary["error_count"] == 0 else "failed", "dataset_name": dataset_name, "exports": payload["exports"]})
    logger.info("Exported signal-ready assets for %d methods", len(method_names))
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_name": dataset_name,
            "sample_id": payload["sample"].sample_id,
            "exports": payload["exports"],
            "validation_summary": summary,
        }
    )
    return 0 if summary["error_count"] == 0 else 1


def cmd_signal_build_report(args: argparse.Namespace) -> int:
    config, project_root, registry = _load_phase3_context(args)
    dataset_name = _phase3_dataset_name(args, config)
    method_names = _phase3_active_methods(args, config)
    context, _ = initialize_run(
        config=config,
        config_path=str(Path(args.config).resolve()),
        command="signal-build-report",
        project_root=project_root,
    )
    logger = configure_logger("gic.phase3.report", config["logging"]["level"], context.log_file)
    payload = _run_phase3_methods(
        config=config,
        project_root=project_root,
        registry=registry,
        dataset_name=dataset_name,
        method_names=method_names,
        export_results=False,
        build_report=True,
    )
    summary = summarize_validation_results(payload["validations"])
    comparison_report = payload["comparison_report"]
    write_summary(
        context,
        {
            "status": "ok" if summary["error_count"] == 0 else "failed",
            "dataset_name": dataset_name,
            "comparison_path": payload["comparison_path"],
            "default_method": comparison_report.default_method if comparison_report else None,
        },
    )
    logger.info("Built Phase 3 comparison report")
    _serialize_result(
        {
            "run_id": context.run_id,
            "dataset_name": dataset_name,
            "sample_id": payload["sample"].sample_id,
            "comparison_path": payload["comparison_path"],
            "comparison_report": signal_to_dict(comparison_report) if comparison_report else None,
            "validation_summary": summary,
        }
    )
    return 0 if summary["error_count"] == 0 else 1


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
