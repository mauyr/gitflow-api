from __future__ import annotations

from dataclasses import dataclass

from gitflow_api.application.context import AppContext
from gitflow_api.application.use_cases.changelog import ChangelogInput, execute as execute_changelog
from gitflow_api.application.use_cases.deploy import execute_profile_for_release
from gitflow_api.domain.exceptions import ConfigError
from gitflow_api.domain.results import LaunchResult
from gitflow_api.git import parse_remote_url


@dataclass(frozen=True)
class LaunchInput:
    version: str
    ref: str | None = None
    deploy_profiles: tuple[str, ...] = ()


def execute(data: LaunchInput, ctx: AppContext) -> LaunchResult:
    remote_url = ctx.git.current_remote_url()
    project_name = parse_remote_url(remote_url).project
    tag_name = ctx.config.changelog.version_tag_pattern.format(project=project_name, version=data.version)

    # The changelog must be calculated before creating this version's tag. Otherwise
    # the freshly created tag becomes the range start and yields empty release notes.
    changelog = execute_changelog(ChangelogInput(version=data.version), ctx)
    ctx.git.create_tag(tag_name, data.version)
    ctx.git.push_tag(tag_name)

    release_name = _render_release_name(ctx.config.launch.release_name_template, project_name, data.version, tag_name)
    release = ctx.provider.create_release(
        remote_url=remote_url,
        tag_name=tag_name,
        name=release_name,
        description=changelog.markdown,
        ref=data.ref,
    )
    deployments = [
        execute_profile_for_release(
            profile_name=profile_name,
            version=data.version,
            tag=tag_name,
            ctx=ctx,
            remote_url=remote_url,
            release=release,
        ).to_dict()
        for profile_name in data.deploy_profiles
    ]

    return LaunchResult(
        ok=True,
        action="launch",
        message="Release tag pushed and platform release created.",
        version=data.version,
        tag=tag_name,
        release=release,
        markdown=changelog.markdown,
        deployments=deployments,
    )


def _render_release_name(template: str, project: str, version: str, tag: str) -> str:
    try:
        rendered = template.format(project=project, version=version, tag=tag).strip()
    except KeyError as exc:
        raise ConfigError(f"Unknown launch.release_name_template variable: {exc.args[0]}") from exc
    if not rendered:
        raise ConfigError("launch.release_name_template rendered an empty release name")
    return rendered
