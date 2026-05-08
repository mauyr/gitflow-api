from __future__ import annotations

import ast
import copy
import os
from pathlib import Path
from typing import Any

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    tomllib = None  # type: ignore[assignment]

from gitflow_api.config.defaults import DEFAULT_CONFIG
from gitflow_api.config.models import (
    AppConfig,
    BehaviorConfig,
    BranchConfig,
    ChangelogConfig,
    MergeRequestConfig,
    ProviderConfig,
)
from gitflow_api.config.validation import ensure_provider_supported, require_non_empty
from gitflow_api.domain.exceptions import ConfigError


def load_config(config_path: str | os.PathLike[str] | None = None) -> AppConfig:
    raw_config = copy.deepcopy(DEFAULT_CONFIG)
    path = _resolve_config_path(config_path)
    if path is not None:
        file_config = _read_toml(path)
        _deep_merge(raw_config, file_config)

    provider_section = raw_config["provider"]
    provider_type = ensure_provider_supported(str(provider_section.get("type", "gitlab")))
    token_env = str(provider_section.get("token_env") or "").strip()
    if not token_env or (
        token_env == str(DEFAULT_CONFIG["provider"].get("token_env", "")).strip()
        and provider_type != str(DEFAULT_CONFIG["provider"].get("type", "gitlab")).strip().lower()
    ):
        token_env = _default_token_env(provider_type)
    token = str(provider_section.get("token") or os.environ.get(token_env, "")).strip()

    provider = ProviderConfig(
        type=provider_type,
        url=require_non_empty(str(provider_section.get("url", "")), "provider.url"),
        token=require_non_empty(token, f"provider.token or env:{token_env}"),
    )

    branches = raw_config["branches"]
    merge_request = raw_config["merge_request"]
    changelog = raw_config["changelog"]
    behavior = raw_config["behavior"]

    return AppConfig(
        provider=provider,
        branches=BranchConfig(
            main=require_non_empty(str(branches.get("main", "")), "branches.main"),
            develop=require_non_empty(str(branches.get("develop", "")), "branches.develop"),
            feature_prefix=require_non_empty(str(branches.get("feature_prefix", "")), "branches.feature_prefix"),
            hotfix_prefix=require_non_empty(str(branches.get("hotfix_prefix", "")), "branches.hotfix_prefix"),
            release_prefix=require_non_empty(str(branches.get("release_prefix", "")), "branches.release_prefix"),
        ),
        merge_request=MergeRequestConfig(
            feature_label=require_non_empty(str(merge_request.get("feature_label", "")), "merge_request.feature_label"),
            hotfix_label=require_non_empty(str(merge_request.get("hotfix_label", "")), "merge_request.hotfix_label"),
            draft_prefix=str(merge_request.get("draft_prefix", "Draft: ")),
            remove_source_branch=bool(merge_request.get("remove_source_branch", True)),
        ),
        changelog=ChangelogConfig(
            output_dir=require_non_empty(str(changelog.get("output_dir", "")), "changelog.output_dir"),
            version_tag_pattern=require_non_empty(
                str(changelog.get("version_tag_pattern", "")), "changelog.version_tag_pattern"
            ),
            include_labels=bool(changelog.get("include_labels", True)),
            feature_labels=list(changelog.get("feature_labels", [])),
            bug_labels=list(changelog.get("bug_labels", [])),
            technical_labels=list(changelog.get("technical_labels", [])),
            ignore_labels=list(changelog.get("ignore_labels", [])),
        ),
        behavior=BehaviorConfig(
            require_clean_worktree=bool(behavior.get("require_clean_worktree", True)),
            auto_push=bool(behavior.get("auto_push", True)),
        ),
    )


def _resolve_config_path(config_path: str | os.PathLike[str] | None) -> Path | None:
    if config_path is not None:
        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
        return path

    for candidate in (Path(".gitflow.toml"), Path("gitflow.toml")):
        if candidate.exists():
            return candidate
    return None


def _read_toml(path: Path) -> dict[str, Any]:
    if tomllib is not None:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
    else:
        data = _read_toml_fallback(path)
    if not isinstance(data, dict):
        raise ConfigError(f"Invalid TOML config structure in {path}")
    return data


def _read_toml_fallback(path: Path) -> dict[str, Any]:
    current_section: dict[str, Any] | None = None
    data: dict[str, Any] = {}

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section_name = line[1:-1].strip()
            current_section = data.setdefault(section_name, {})
            continue
        if current_section is None or "=" not in line:
            raise ConfigError(f"Unsupported TOML content in fallback parser: {raw_line}")

        key, raw_value = [part.strip() for part in line.split("=", 1)]
        current_section[key] = _parse_toml_value(raw_value)

    return data


def _parse_toml_value(raw_value: str) -> Any:
    lowered = raw_value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    try:
        return ast.literal_eval(raw_value)
    except (SyntaxError, ValueError):
        return raw_value.strip('"')


def _default_token_env(provider_type: str) -> str:
    if provider_type == "github":
        return "GITHUB_TOKEN"
    return "GITFLOW_GITLAB_TOKEN"


def _deep_merge(base: dict[str, Any], incoming: dict[str, Any]) -> None:
    for key, value in incoming.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
