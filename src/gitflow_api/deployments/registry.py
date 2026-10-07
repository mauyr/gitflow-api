from __future__ import annotations

from importlib.metadata import entry_points

from gitflow_api.deployments.base import DeploymentEvent, DeploymentExecution, DeploymentExtension
from gitflow_api.deployments.command import CommandDeploymentExtension
from gitflow_api.deployments.digitalocean_apps import DigitalOceanAppsDeploymentExtension
from gitflow_api.domain.exceptions import DeploymentError


def execute_profile(event: DeploymentEvent) -> DeploymentExecution:
    if event.profile.options.get("enabled", True) is not True:
        raise DeploymentError(f"Deployment profile is disabled: {event.profile.name}")
    extension = _extensions().get(event.profile.driver)
    if extension is None:
        available = ", ".join(sorted(_extensions())) or "none"
        raise DeploymentError(f"Unknown deployment driver '{event.profile.driver}'. Available drivers: {available}")
    return extension.execute(event)


def _extensions() -> dict[str, DeploymentExtension]:
    extensions: dict[str, DeploymentExtension] = {
        CommandDeploymentExtension.name: CommandDeploymentExtension(),
        DigitalOceanAppsDeploymentExtension.name: DigitalOceanAppsDeploymentExtension(),
    }
    discovered = entry_points()
    group = discovered.select(group="gitflow_api.deployment_extensions") if hasattr(discovered, "select") else discovered.get("gitflow_api.deployment_extensions", [])
    for entry_point in group:
        candidate = entry_point.load()
        extension = candidate() if isinstance(candidate, type) else candidate
        name = getattr(extension, "name", None)
        execute = getattr(extension, "execute", None)
        if not isinstance(name, str) or not name or not callable(execute):
            raise DeploymentError(f"Invalid deployment extension entry point: {entry_point.name}")
        extensions[name] = extension
    return extensions
