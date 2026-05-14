from __future__ import annotations

import subprocess
from pathlib import Path

from gitflow_api.domain.exceptions import BranchNotFoundError, ChangelogError, RepositoryError
from gitflow_api.git.models import GitCommandResult


class GitClient:
    def __init__(self, repo_path: str | Path = ".") -> None:
        self.repo_path = Path(repo_path).resolve()

    def current_branch(self) -> str:
        return self._run(["git", "branch", "--show-current"]).stdout.strip()

    def current_remote_url(self, remote: str = "origin") -> str:
        return self._run(["git", "remote", "get-url", remote]).stdout.strip()

    def is_worktree_clean(self) -> bool:
        return not self._run(["git", "status", "--porcelain"]).stdout.strip()

    def checkout(self, branch: str) -> None:
        result = self._run(["git", "checkout", branch], check=False)
        if result.returncode != 0:
            raise BranchNotFoundError(result.stderr.strip() or f"Branch not found: {branch}")

    def pull(self, branch: str | None = None) -> None:
        command = ["git", "pull"] if branch is None else ["git", "pull", "origin", branch]
        self._run(command)

    def create_branch(self, new_branch: str, from_branch: str) -> None:
        self.checkout(from_branch)
        self.pull(from_branch)
        self._run(["git", "checkout", "-b", new_branch])

    def push(self, branch: str, set_upstream: bool = True) -> None:
        command = ["git", "push"]
        if set_upstream:
            command.extend(["-u", "origin", branch])
        else:
            command.append(branch)
        self._run(command)

    def local_branch_exists(self, branch: str) -> bool:
        result = self._run(["git", "show-ref", "--verify", f"refs/heads/{branch}"], check=False)
        return result.returncode == 0

    def remote_branch_exists(self, branch: str) -> bool:
        result = self._run(["git", "ls-remote", "--heads", "origin", branch], check=False)
        return bool(result.stdout.strip())

    def create_tag(self, tag: str, message: str | None = None) -> None:
        command = ["git", "tag", "-a", tag]
        if message:
            command.extend(["-m", message])
        self._run(command)

    def push_tag(self, tag: str) -> None:
        self._run(["git", "push", "origin", tag])

    def delete_tag(self, tag: str) -> None:
        self._run(["git", "tag", "-d", tag])

    def latest_tag(self) -> str | None:
        result = self._run(
            ["git", "for-each-ref", "--sort=-creatordate", "--format=%(refname:strip=2)", "refs/tags"],
            check=False,
        )
        tags = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return tags[0] if tags else None

    def resolve_commit(self, ref: str) -> str:
        result = self._run(["git", "rev-parse", "--verify", f"{ref}^{{commit}}"], check=False)
        commit = result.stdout.strip()
        if result.returncode != 0 or not commit:
            raise ChangelogError(f"Invalid from-ref: {ref}")
        return commit

    def log(self, revspec: str | None = None) -> str:
        command = ["git", "log"] if revspec is None else ["git", "log", revspec]
        return self._run(command).stdout

    def _run(self, command: list[str], check: bool = True) -> GitCommandResult:
        process = subprocess.run(
            command,
            cwd=self.repo_path,
            text=True,
            capture_output=True,
            check=False,
        )
        result = GitCommandResult(
            command=command,
            returncode=process.returncode,
            stdout=process.stdout,
            stderr=process.stderr,
        )
        if check and process.returncode != 0:
            raise RepositoryError(result.stderr.strip() or f"Git command failed: {' '.join(command)}")
        return result
