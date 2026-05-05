from __future__ import annotations

from gitflow_api.domain.exceptions import ProviderError
from gitflow_api.git import parse_remote_url


class GitLabProjectResolver:
    def __init__(self, gitlab_client) -> None:
        self.gitlab_client = gitlab_client

    def resolve(self, remote_url: str):
        remote = parse_remote_url(remote_url)
        try:
            return self.gitlab_client.projects.get(remote.full_path)
        except Exception as exc:
            raise ProviderError(f"GitLab project not found for remote '{remote.full_path}'") from exc
