from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from gitflow_api.deployments.base import DeploymentEvent, DeploymentExecution
from gitflow_api.domain.exceptions import DeploymentError


class CommandDeploymentExtension:
    """Runs a trusted, configured deployment command without invoking a shell."""

    name = "command"

    def execute(self, event: DeploymentEvent) -> DeploymentExecution:
        command = _command_from_options(event.profile.options)
        rendered_command = [_render(value, event) for value in command]
        working_directory = _working_directory(event)
        timeout_seconds = _timeout_seconds(event.profile.options)
        metadata = {
            "command": rendered_command,
            "working_directory": str(working_directory),
            "timeout_seconds": timeout_seconds,
        }

        if event.dry_run:
            return DeploymentExecution(
                profile=event.profile.name,
                driver=self.name,
                status="planned",
                message="Deployment command validated; dry run did not execute it.",
                metadata=metadata,
            )

        try:
            process = subprocess.run(
                rendered_command,
                cwd=working_directory,
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise DeploymentError(f"Deployment command was not found: {rendered_command[0]}") from exc
        except subprocess.TimeoutExpired as exc:
            raise DeploymentError(f"Deployment command timed out after {timeout_seconds} seconds") from exc

        if process.returncode != 0:
            details = process.stderr.strip() or process.stdout.strip() or "no command output"
            raise DeploymentError(f"Deployment command failed ({process.returncode}): {details}")

        return DeploymentExecution(
            profile=event.profile.name,
            driver=self.name,
            status="started",
            message="Deployment command completed successfully.",
            metadata=metadata,
        )


def _command_from_options(options: dict[str, Any]) -> list[str]:
    command = options.get("command")
    if not isinstance(command, list) or not command or not all(isinstance(item, str) and item.strip() for item in command):
        raise DeploymentError("Deployment profile using driver 'command' requires a non-empty string array: command")
    return command


def _working_directory(event: DeploymentEvent) -> Path:
    raw_path = event.profile.options.get("working_directory")
    if raw_path is None:
        return Path(event.repo_path)
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise DeploymentError("deployment working_directory must be a non-empty string")
    rendered = _render(raw_path, event)
    path = Path(rendered)
    if not path.is_absolute():
        path = Path(event.repo_path) / path
    if not path.is_dir():
        raise DeploymentError(f"Deployment working directory does not exist: {path}")
    return path


def _timeout_seconds(options: dict[str, Any]) -> int:
    value = options.get("timeout_seconds", 1800)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise DeploymentError("deployment timeout_seconds must be a positive integer")
    return value


def _render(value: str, event: DeploymentEvent) -> str:
    release_url = ""
    if isinstance(event.release, dict):
        release_url = str(event.release.get("url", ""))
    try:
        return value.format(
            version=event.version,
            tag=event.tag,
            repo_path=event.repo_path,
            remote_url=event.remote_url,
            release_url=release_url,
        )
    except KeyError as exc:
        raise DeploymentError(f"Unknown deployment template variable: {exc.args[0]}") from exc
