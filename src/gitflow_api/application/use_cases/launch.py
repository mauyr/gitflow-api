from __future__ import annotations

from dataclasses import dataclass

from gitflow_api.application.context import AppContext
from gitflow_api.application.use_cases.changelog import ChangelogInput, execute as execute_changelog
from gitflow_api.domain.results import LaunchResult
from gitflow_api.git import parse_remote_url


@dataclass(frozen=True)
class LaunchInput:
    version: str
    ref: str | None = None


def execute(data: LaunchInput, ctx: AppContext) -> LaunchResult:
    remote_url = ctx.git.current_remote_url()
    project_name = parse_remote_url(remote_url).project
    tag_name = ctx.config.changelog.version_tag_pattern.format(project=project_name, version=data.version)

    ctx.git.create_tag(tag_name, data.version)
    ctx.git.push_tag(tag_name)

    changelog = execute_changelog(ChangelogInput(version=data.version), ctx)
    release = ctx.provider.create_release(
        remote_url=remote_url,
        tag_name=tag_name,
        name=f"{project_name} {data.version}",
        description=changelog.markdown,
        ref=data.ref,
    )

    return LaunchResult(
        ok=True,
        action="launch",
        message="Release tag pushed and platform release created.",
        version=data.version,
        tag=tag_name,
        release=release,
        markdown=changelog.markdown,
    )
