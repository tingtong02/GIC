from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from pathlib import Path
from typing import Any

from gic.config import dump_config, load_config
from gic.utils.logging_utils import configure_logger
from gic.utils.runtime import initialize_run, write_summary

DEFAULT_CONFIG = "configs/phase0/phase0_dev.yaml"


def _common_run_parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default=DEFAULT_CONFIG, help="Path to the config file")
    parser.add_argument(
        "--project-root",
        default=None,
        help="Optional project root override for writing artifacts, logs, and reports",
    )


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

    return parser


def _serialize_result(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


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
    except Exception as exc:  # pragma: no cover - environment dependent
        payload["torch"] = {"error": f"{type(exc).__name__}: {exc}"}
    _serialize_result(payload)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
