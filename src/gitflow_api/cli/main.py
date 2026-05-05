from __future__ import annotations

import argparse
import json
from dataclasses import asdict, is_dataclass

from gitflow_api import __version__
from gitflow_api.application.factories import build_context
from gitflow_api.application.use_cases import (
    FeatureFinishInput,
    FeatureStartInput,
    HotfixFinishInput,
    HotfixStartInput,
    execute_feature_finish,
    execute_feature_start,
    execute_hotfix_finish,
    execute_hotfix_start,
)
from gitflow_api.config import load_config
from gitflow_api.domain.exceptions import GitflowError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gitflow-next", description="Modernized gitflow-api CLI bootstrap")
    parser.add_argument("--config", dest="config_path", help="Path to .gitflow.toml")
    parser.add_argument("--repo", dest="repo_path", help="Path to the target git repository")
    parser.add_argument("--json", action="store_true", dest="as_json", help="Render machine-friendly JSON output")

    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    subparsers.add_parser("version", help="Show package version")
    subparsers.add_parser("config-check", help="Validate configuration loading")

    feature_parser = subparsers.add_parser("feature", help="Feature branch workflows")
    feature_sub = feature_parser.add_subparsers(dest="feature_command")
    feature_sub.required = True
    feature_start = feature_sub.add_parser("start", help="Create feature branch and MR")
    feature_start.add_argument("name")
    feature_start.add_argument("--title")
    feature_start.add_argument("--issue")
    feature_start.add_argument("--description")
    feature_start.add_argument("--draft", action=argparse.BooleanOptionalAction, default=True)
    feature_finish = feature_sub.add_parser("finish", help="Merge feature MR")
    feature_finish.add_argument("branch", nargs="?")

    hotfix_parser = subparsers.add_parser("hotfix", help="Hotfix branch workflows")
    hotfix_sub = hotfix_parser.add_subparsers(dest="hotfix_command")
    hotfix_sub.required = True
    hotfix_start = hotfix_sub.add_parser("start", help="Create hotfix branch and MR")
    hotfix_start.add_argument("name")
    hotfix_start.add_argument("--title")
    hotfix_start.add_argument("--issue")
    hotfix_start.add_argument("--description")
    hotfix_start.add_argument("--draft", action=argparse.BooleanOptionalAction, default=True)
    hotfix_finish = hotfix_sub.add_parser("finish", help="Merge hotfix MR")
    hotfix_finish.add_argument("branch", nargs="?")

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
        if args.command == "feature":
            ctx = build_context(repo_path=args.repo_path, config_path=args.config_path)
            if args.feature_command == "start":
                result = execute_feature_start(
                    FeatureStartInput(
                        name=args.name,
                        title=args.title,
                        issue=args.issue,
                        draft=args.draft,
                        description=args.description,
                    ),
                    ctx,
                )
                return _emit(_to_payload(result), args.as_json)
            if args.feature_command == "finish":
                result = execute_feature_finish(FeatureFinishInput(branch=args.branch), ctx)
                return _emit(_to_payload(result), args.as_json)
        if args.command == "hotfix":
            ctx = build_context(repo_path=args.repo_path, config_path=args.config_path)
            if args.hotfix_command == "start":
                result = execute_hotfix_start(
                    HotfixStartInput(
                        name=args.name,
                        title=args.title,
                        issue=args.issue,
                        draft=args.draft,
                        description=args.description,
                    ),
                    ctx,
                )
                return _emit(_to_payload(result), args.as_json)
            if args.hotfix_command == "finish":
                result = execute_hotfix_finish(HotfixFinishInput(branch=args.branch), ctx)
                return _emit(_to_payload(result), args.as_json)
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
        elif payload.get("action"):
            print(payload.get("message", "OK"))
            if payload.get("branch"):
                print(f"branch: {payload['branch']}")
            merge_request = payload.get("merge_request")
            if isinstance(merge_request, dict) and merge_request.get("url"):
                print(f"merge_request: {merge_request['url']}")
        else:
            print("Config OK")
    return 0


def _to_payload(result) -> dict:
    if is_dataclass(result):
        return asdict(result)
    return result


def _emit_error(exc: Exception, as_json: bool) -> int:
    payload = {"ok": False, "error": {"type": exc.__class__.__name__, "message": str(exc)}}
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"ERROR: {exc}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
