from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass

from gitflow_api import __version__
from gitflow_api.config import load_config
from gitflow_api.domain.exceptions import GitflowError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gitflow-next", description="Modernized gitflow-api CLI bootstrap")
    parser.add_argument("--config", dest="config_path", help="Path to .gitflow.toml")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Render machine-friendly JSON output")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    subparsers.add_parser("version", help="Show package version")
    subparsers.add_parser("config-check", help="Validate configuration loading")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "version":
            return _emit({"ok": True, "version": __version__}, args.as_json)
        if args.command == "config-check":
            config = load_config(args.config_path)
            payload = asdict(config) if is_dataclass(config) else config
            payload = {"ok": True, "config": payload}
            return _emit(payload, args.as_json)
        parser.error(f"Unknown command: {args.command}")
    except GitflowError as exc:
        return _emit_error(exc, args.as_json)

    return 1


def _emit(payload: dict, as_json: bool) -> int:
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        if "version" in payload:
            print(payload["version"])
        else:
            print("Config OK")
    return 0


def _emit_error(exc: Exception, as_json: bool) -> int:
    payload = {"ok": False, "error": {"type": exc.__class__.__name__, "message": str(exc)}}
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"ERROR: {exc}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
