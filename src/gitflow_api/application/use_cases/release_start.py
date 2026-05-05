from __future__ import annotations

from dataclasses import dataclass

from gitflow_api.application.context import AppContext
from gitflow_api.application.use_cases.common import start_branch
from gitflow_api.application.use_cases.release_common import ensure_release_flow_enabled
from gitflow_api.domain.results import ReleaseStartResult


@dataclass(frozen=True)
class ReleaseStartInput:
    version: str
    title: str | None = None
    draft: bool = False
    description: str | None = None


def execute(data: ReleaseStartInput, ctx: AppContext) -> ReleaseStartResult:
    ensure_release_flow_enabled(ctx)
    branch = f"{ctx.config.branches.release_prefix}{data.version}"
    start_branch(ctx, branch, ctx.config.branches.develop)

    remote_url = ctx.git.current_remote_url()
    merge_request = ctx.provider.create_merge_request(
        remote_url=remote_url,
        source_branch=branch,
        target_branch=ctx.config.branches.main,
        title=data.title or f"Release {data.version}",
        description=data.description,
        labels=[],
        draft=data.draft,
        remove_source_branch=ctx.config.merge_request.remove_source_branch,
    )

    return ReleaseStartResult(
        ok=True,
        action="release_start",
        message="Release branch created and merge request opened.",
        branch=branch,
        version=data.version,
        merge_request=merge_request.__dict__,
    )
