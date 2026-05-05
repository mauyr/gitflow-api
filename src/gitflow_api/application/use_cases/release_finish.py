from __future__ import annotations

from dataclasses import dataclass

from gitflow_api.application.context import AppContext
from gitflow_api.application.use_cases.release_common import ensure_release_flow_enabled
from gitflow_api.domain.results import ReleaseFinishResult


@dataclass(frozen=True)
class ReleaseFinishInput:
    branch: str | None = None
    create_sync_merge_request: bool = True


def execute(data: ReleaseFinishInput, ctx: AppContext) -> ReleaseFinishResult:
    ensure_release_flow_enabled(ctx)
    branch = data.branch or ctx.git.current_branch()
    remote_url = ctx.git.current_remote_url()

    ready_merge_request = ctx.provider.validate_merge_request_ready(
        remote_url=remote_url,
        source_branch=branch,
        target_branch=ctx.config.branches.main,
    )
    merged_merge_request = ctx.provider.merge_merge_request(
        remote_url=remote_url,
        source_branch=branch,
        target_branch=ctx.config.branches.main,
    )

    sync_merge_request = None
    if data.create_sync_merge_request:
        sync_title = f"Sync {ctx.config.branches.main} into {ctx.config.branches.develop} after {branch}"
        sync_merge_request = ctx.provider.create_merge_request(
            remote_url=remote_url,
            source_branch=ctx.config.branches.main,
            target_branch=ctx.config.branches.develop,
            title=sync_title,
            description="Automatic synchronization merge request created after finishing release flow.",
            labels=[],
            draft=False,
            remove_source_branch=False,
        )

    ctx.git.checkout(ctx.config.branches.main)
    ctx.git.pull(ctx.config.branches.main)

    return ReleaseFinishResult(
        ok=True,
        action="release_finish",
        message="Release merge request merged into main.",
        branch=branch,
        merged_to=ctx.config.branches.main,
        merge_request=(merged_merge_request or ready_merge_request).__dict__,
        sync_merge_request=None if sync_merge_request is None else sync_merge_request.__dict__,
    )
