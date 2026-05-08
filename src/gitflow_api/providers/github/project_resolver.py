from __future__ import annotations

from gitflow_api.git import parse_remote_url


class GitHubProjectResolver:
    def resolve(self, remote_url: str) -> tuple[str, str, str]:
        remote = parse_remote_url(remote_url)
        owner = remote.namespace.split("/")[0]
        return owner, remote.project, remote.full_path
