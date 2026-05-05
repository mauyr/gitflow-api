from __future__ import annotations

from gitflow_api.application.context import AppContext
from gitflow_api.domain.exceptions import ReleaseFlowError


def ensure_release_flow_enabled(ctx: AppContext) -> None:
    if ctx.config.branches.main == ctx.config.branches.develop:
        raise ReleaseFlowError(
            "Release flow requires distinct main and develop branches in project configuration."
        )
