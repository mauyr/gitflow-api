from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from gitflow_api.deployments.base import DeploymentEvent, DeploymentExecution
from gitflow_api.domain.exceptions import DeploymentError


class DigitalOceanAppsDeploymentExtension:
    """Starts a DigitalOcean App Platform deployment through the locally authenticated doctl CLI."""

    name = "digitalocean-app"

    def execute(self, event: DeploymentEvent) -> DeploymentExecution:
        app_id = _required_string(event.profile.options, "app_id")
        components = event.profile.options.get("components")
        if not isinstance(components, list) or not components:
            raise DeploymentError(
                "DigitalOcean App deployments require a non-empty components list so every released source is verified."
            )

        validation = _validate_components(components, event.version, event.dry_run)
        command = _build_command(event, app_id)
        metadata: dict[str, Any] = {"app_id": app_id, "components": validation, "command": command}

        if event.dry_run:
            return DeploymentExecution(
                profile=event.profile.name,
                driver=self.name,
                status="planned",
                message="DigitalOcean App deployment prerequisites validated; dry run did not start it.",
                metadata=metadata,
            )

        executable = command[0]
        if shutil.which(executable) is None:
            raise DeploymentError(f"DigitalOcean deployment requires '{executable}' on PATH")

        timeout_seconds = _timeout_seconds(event.profile.options)
        try:
            process = subprocess.run(
                command,
                cwd=Path(event.repo_path),
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise DeploymentError(f"DigitalOcean deployment timed out after {timeout_seconds} seconds") from exc

        if process.returncode != 0:
            details = process.stderr.strip() or process.stdout.strip() or "no doctl output"
            raise DeploymentError(f"DigitalOcean deployment failed ({process.returncode}): {details}")

        metadata.update(_deployment_metadata(process.stdout))
        return DeploymentExecution(
            profile=event.profile.name,
            driver=self.name,
            status="started",
            message="DigitalOcean App deployment completed successfully.",
            metadata=metadata,
        )


def _build_command(event: DeploymentEvent, app_id: str) -> list[str]:
    options = event.profile.options
    executable = str(options.get("doctl", "doctl"))
    command = [executable]
    context = options.get("context")
    if context is not None:
        if not isinstance(context, str) or not context.strip():
            raise DeploymentError("DigitalOcean deployment context must be a non-empty string")
        command.extend(["--context", context])
    command.extend(["--output", "json", "apps", "create-deployment", app_id])
    if bool(options.get("wait", True)):
        command.append("--wait")
    if bool(options.get("force_rebuild", False)):
        command.append("--force-rebuild")
    return command


def _validate_components(components: list[Any], version: str, dry_run: bool) -> list[dict[str, str]]:
    validated: list[dict[str, str]] = []
    for index, raw_component in enumerate(components, start=1):
        if not isinstance(raw_component, dict):
            raise DeploymentError(f"deploy.components[{index}] must be a table")
        raw_path = _required_string(raw_component, "path", label=f"deploy.components[{index}].path")
        branch = str(raw_component.get("branch", "master"))
        tag_template = str(raw_component.get("tag", "{version}"))
        try:
            tag = tag_template.format(version=version)
        except KeyError as exc:
            raise DeploymentError(f"Unknown component tag template variable: {exc.args[0]}") from exc

        path = Path(raw_path).expanduser().resolve()
        if not path.is_dir() or not (path / ".git").exists():
            raise DeploymentError(f"Deployment component is not a git repository: {path}")
        if dry_run:
            _run_git(path, ["status", "--porcelain"])
        else:
            _run_git(path, ["fetch", "origin", branch, "--tags"])
        dirty = _run_git(path, ["status", "--porcelain"])
        if dirty:
            raise DeploymentError(f"Deployment component has uncommitted changes: {path}")
        tag_commit = _run_git(path, ["rev-parse", "--verify", f"{tag}^{{commit}}"])
        branch_commit = _run_git(path, ["rev-parse", "--verify", f"origin/{branch}^{{commit}}"])
        if tag_commit != branch_commit:
            raise DeploymentError(
                f"Deployment component is not pinned to release {version}: {path} tag {tag} != origin/{branch}"
            )
        validated.append({"path": str(path), "branch": branch, "tag": tag, "commit": tag_commit})
    return validated


def _run_git(path: Path, args: list[str]) -> str:
    process = subprocess.run(["git", *args], cwd=path, text=True, capture_output=True, check=False)
    if process.returncode != 0:
        details = process.stderr.strip() or process.stdout.strip() or "no git output"
        raise DeploymentError(f"Git validation failed in {path}: {details}")
    return process.stdout.strip()


def _required_string(options: dict[str, Any], key: str, *, label: str | None = None) -> str:
    value = options.get(key)
    if not isinstance(value, str) or not value.strip():
        raise DeploymentError(f"Deployment profile requires {label or key}")
    return value.strip()


def _timeout_seconds(options: dict[str, Any]) -> int:
    value = options.get("timeout_seconds", 1800)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise DeploymentError("deployment timeout_seconds must be a positive integer")
    return value


def _deployment_metadata(output: str) -> dict[str, Any]:
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return {}
    deployment = parsed[0] if isinstance(parsed, list) and parsed else parsed
    if not isinstance(deployment, dict):
        return {}
    metadata: dict[str, Any] = {}
    for key in ("id", "phase", "progress", "cause"):
        value = deployment.get(key) or deployment.get(key.title())
        if value is not None:
            metadata[f"deployment_{key}"] = value
    return metadata
