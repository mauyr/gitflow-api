from __future__ import annotations

from dataclasses import dataclass

from gitflow_api.application.context import AppContext
from gitflow_api.domain.results import FeatureFinishResult


@dataclass(frozen=True)
class FeatureFinishInput:
    branch: str | None = None


def execute(data: FeatureFinishInput, ctx: AppContext) -> FeatureFinishResult:
    branch = data.branch or ctx.git.current_branch()
    remote_url = ctx.git.current_remote_url()

    ready_merge_request = ctx.provider.validate_merge_request_ready(
        remote_url=remote_url,
        source_branch=branch,
        target_branch=ctx.config.branches.develop,
    )
    merged_merge_request = ctx.provider.merge_merge_request(
        remote_url=remote_url,
        source_branch=branch,
        target_branch=ctx.config.branches.develop,
    )

    ctx.git.checkout(ctx.config.branches.develop)
    ctx.git.pull(ctx.config.branches.develop)

    return FeatureFinishResult(
        ok=True,
        action="feature_finish",
        message="Feature merge request merged into develop.",
        branch=branch,
        merged_to=ctx.config.branches.develop,
        merge_request=(merged_merge_request or ready_merge_request).__dict__,
    )
