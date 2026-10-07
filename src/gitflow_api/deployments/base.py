from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from gitflow_api.config.models import DeploymentProfileConfig


@dataclass(frozen=True)
class DeploymentEvent:
    profile: DeploymentProfileConfig
    version: str
    tag: str
    repo_path: str
    remote_url: str
    release: dict[str, Any] | None = None
    dry_run: bool = False


@dataclass(frozen=True)
class DeploymentExecution:
    profile: str
    driver: str
    status: str
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "profile": self.profile,
            "driver": self.driver,
            "status": self.status,
            "message": self.message,
            "metadata": self.metadata,
        }


class DeploymentExtension(Protocol):
    name: str

    def execute(self, event: DeploymentEvent) -> DeploymentExecution:
        ...
