from __future__ import annotations

from dataclasses import dataclass

from gitflow_api.application.context import AppContext
from gitflow_api.config.models import DeploymentProfileConfig
from gitflow_api.deployments import DeploymentEvent, execute_profile
from gitflow_api.domain.exceptions import DeploymentError
from gitflow_api.domain.results import DeployResult
from gitflow_api.git import parse_remote_url


@dataclass(frozen=True)
class DeployInput:
    profile: str
    version: str
    dry_run: bool = False


def execute(data: DeployInput, ctx: AppContext) -> DeployResult:
    remote_url = ctx.git.current_remote_url()
    project_name = parse_remote_url(remote_url).project
    tag_name = ctx.config.changelog.version_tag_pattern.format(project=project_name, version=data.version)
    execution = execute_profile_for_release(
        profile_name=data.profile,
        version=data.version,
        tag=tag_name,
        ctx=ctx,
        remote_url=remote_url,
        release=None,
        dry_run=data.dry_run,
    )
    message = "Deployment validation completed." if data.dry_run else "Deployment completed successfully."
    return DeployResult(
        ok=True,
        action="deploy",
        message=message,
        profile=data.profile,
        version=data.version,
        tag=tag_name,
        deployments=[execution.to_dict()],
        dry_run=data.dry_run,
    )


def execute_profile_for_release(
    *,
    profile_name: str,
    version: str,
    tag: str,
    ctx: AppContext,
    remote_url: str,
    release: dict | None,
    dry_run: bool = False,
):
    profile = _find_profile(ctx.config.deploy.profiles, profile_name)
    return execute_profile(
        DeploymentEvent(
            profile=profile,
            version=version,
            tag=tag,
            repo_path=ctx.repo_path,
            remote_url=remote_url,
            release=release,
            dry_run=dry_run,
        )
    )


def _find_profile(profiles: list[DeploymentProfileConfig], profile_name: str) -> DeploymentProfileConfig:
    for profile in profiles:
        if profile.name == profile_name:
            return profile
    raise DeploymentError(f"Deployment profile not found: {profile_name}")
