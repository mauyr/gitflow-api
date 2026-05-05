from __future__ import annotations

from dataclasses import dataclass

from gitflow_api.application.context import AppContext
from gitflow_api.domain.results import FeatureFinishResult


@dataclass(frozen=True)
class HotfixFinishInput:
    branch: str | None = None


def execute(data: HotfixFinishInput, ctx: AppContext) -> FeatureFinishResult:
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

    ctx.git.checkout(ctx.config.branches.main)
    ctx.git.pull(ctx.config.branches.main)

    return FeatureFinishResult(
        ok=True,
        action="hotfix_finish",
        message="Hotfix merge request merged into main.",
        branch=branch,
        merged_to=ctx.config.branches.main,
        merge_request=(merged_merge_request or ready_merge_request).__dict__,
    )
