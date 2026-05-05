from __future__ import annotations

from dataclasses import dataclass

from gitflow_api.application.context import AppContext
from gitflow_api.application.use_cases.common import start_branch
from gitflow_api.domain.results import FeatureStartResult


@dataclass(frozen=True)
class FeatureStartInput:
    name: str
    title: str | None = None
    issue: str | None = None
    draft: bool = True
    description: str | None = None


def execute(data: FeatureStartInput, ctx: AppContext) -> FeatureStartResult:
    branch = f"{ctx.config.branches.feature_prefix}{data.name}"
    start_branch(ctx, branch, ctx.config.branches.develop)

    remote_url = ctx.git.current_remote_url()
    title = data.title or data.name
    merge_request = ctx.provider.create_merge_request(
        remote_url=remote_url,
        source_branch=branch,
        target_branch=ctx.config.branches.develop,
        title=title,
        description=data.description,
        labels=[ctx.config.merge_request.feature_label],
        draft=data.draft,
        remove_source_branch=ctx.config.merge_request.remove_source_branch,
    )

    return FeatureStartResult(
        ok=True,
        action="feature_start",
        message="Feature branch created and merge request opened.",
        branch=branch,
        base_branch=ctx.config.branches.develop,
        merge_request=merge_request.__dict__,
    )
