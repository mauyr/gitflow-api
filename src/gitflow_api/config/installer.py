from __future__ import annotations

import copy
import getpass
import json
from dataclasses import dataclass
from pathlib import Path

from gitflow_api.config.defaults import DEFAULT_CONFIG
from gitflow_api.config.loader import default_global_config_path
from gitflow_api.config.validation import ensure_provider_supported, require_non_empty
from gitflow_api.domain.exceptions import ConfigError


@dataclass(frozen=True)
class InstallConfigResult:
    ok: bool
    action: str
    message: str
    path: str
    scope: str
    provider: str


def install_config(
    *,
    repo_path: str | None = None,
    scope: str | None = None,
    provider: str | None = None,
    token: str | None = None,
    url: str | None = None,
    force: bool = False,
    interactive: bool = True,
) -> InstallConfigResult:
    resolved_scope = _resolve_scope(scope, interactive)
    resolved_provider = _resolve_provider(provider, interactive)
    resolved_url = _resolve_url(url, resolved_provider)
    resolved_token = _resolve_token(token, interactive)
    target_path = _target_path(resolved_scope, repo_path)

    if target_path.exists() and not force:
        if not interactive or not _confirm(f"Config file already exists at {target_path}. Overwrite?"):
            raise ConfigError(f"Config file already exists: {target_path}")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        render_config(provider=resolved_provider, url=resolved_url, token=resolved_token),
        encoding="utf-8",
    )

    return InstallConfigResult(
        ok=True,
        action="install",
        message="Gitflow configuration installed.",
        path=str(target_path),
        scope=resolved_scope,
        provider=resolved_provider,
    )


def render_config(*, provider: str, url: str, token: str) -> str:
    provider_type = ensure_provider_supported(provider)
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["provider"] = {
        "type": provider_type,
        "url": require_non_empty(url, "provider.url"),
        "token": require_non_empty(token, "provider.token"),
    }
    if provider_type == "github":
        config["merge_request"]["feature_label"] = "feature"
        config["changelog"]["feature_labels"] = ["story", "feature", "change", "enhancement"]
        config["changelog"]["technical_labels"] = ["technical-debt"]

    return "\n".join(
        [
            _section("provider", config["provider"]),
            _section("branches", config["branches"]),
            _section("merge_request", config["merge_request"]),
            _section("changelog", config["changelog"]),
            _section("behavior", config["behavior"]),
            "",
        ]
    )


def _target_path(scope: str, repo_path: str | None) -> Path:
    if scope == "global":
        return default_global_config_path()
    return Path(repo_path or ".").resolve() / "gitflow.toml"


def _resolve_scope(value: str | None, interactive: bool) -> str:
    if value:
        normalized = value.strip().lower()
        if normalized in {"project", "global"}:
            return normalized
        raise ConfigError("install scope must be 'project' or 'global'")
    if not interactive:
        raise ConfigError("install scope is required in non-interactive mode")
    return _prompt_choice("Create configuration scope", ("project", "global"), default="project")


def _resolve_provider(value: str | None, interactive: bool) -> str:
    if value:
        return ensure_provider_supported(value)
    if not interactive:
        raise ConfigError("provider is required in non-interactive mode")
    return _prompt_choice("Provider", ("github", "gitlab"), default="github")


def _resolve_url(value: str | None, provider: str) -> str:
    if value:
        return value.strip()
    if provider == "github":
        return "https://github.com"
    return "https://gitlab.com"


def _resolve_token(value: str | None, interactive: bool) -> str:
    if value:
        return value.strip()
    if not interactive:
        raise ConfigError("provider token is required in non-interactive mode")
    return getpass.getpass("Provider token: ").strip()


def _prompt_choice(label: str, options: tuple[str, ...], *, default: str) -> str:
    choices = "/".join(options)
    raw = input(f"{label} ({choices}) [{default}]: ").strip().lower()
    value = raw or default
    if value not in options:
        raise ConfigError(f"Invalid choice for {label}: {value}")
    return value


def _confirm(label: str) -> bool:
    raw = input(f"{label} [y/N]: ").strip().lower()
    return raw in {"y", "yes", "s", "sim"}


def _section(name: str, values: dict) -> str:
    lines = [f"[{name}]"]
    for key, value in values.items():
        lines.append(f"{key} = {_toml_value(value)}")
    return "\n".join(lines)


def _toml_value(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    return json.dumps(str(value), ensure_ascii=False)
