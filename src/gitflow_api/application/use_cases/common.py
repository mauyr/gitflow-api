from __future__ import annotations

from gitflow_api.application.context import AppContext
from gitflow_api.domain.exceptions import BranchAlreadyExistsError, WorkingTreeNotCleanError


def ensure_clean_worktree(ctx: AppContext) -> None:
    if ctx.config.behavior.require_clean_worktree and not ctx.git.is_worktree_clean():
        raise WorkingTreeNotCleanError("Working tree has uncommitted changes.")


def ensure_branch_available(ctx: AppContext, branch: str) -> None:
    if ctx.git.local_branch_exists(branch) or ctx.git.remote_branch_exists(branch):
        raise BranchAlreadyExistsError(f"Branch already exists: {branch}")


def start_branch(ctx: AppContext, branch: str, from_branch: str) -> None:
    ensure_clean_worktree(ctx)
    ensure_branch_available(ctx, branch)
    ctx.git.create_branch(branch, from_branch)
    if ctx.config.behavior.auto_push:
        ctx.git.push(branch, set_upstream=True)
