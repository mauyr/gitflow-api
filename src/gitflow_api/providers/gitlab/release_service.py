from __future__ import annotations

from gitflow_api.domain.exceptions import ProviderError
from gitflow_api.providers.gitlab.project_resolver import GitLabProjectResolver


class GitLabReleaseService:
    def __init__(self, gitlab_client) -> None:
        self.gitlab_client = gitlab_client
        self.project_resolver = GitLabProjectResolver(gitlab_client)

    def create(self, remote_url: str, tag_name: str, name: str, description: str, ref: str | None = None) -> dict:
        project = self.project_resolver.resolve(remote_url)
        payload = {
            "name": name,
            "tag_name": tag_name,
            "description": description,
        }
        if ref:
            payload["ref"] = ref
        try:
            release = project.releases.create(payload)
        except Exception as exc:
            raise ProviderError(f"Failed to create GitLab release for tag '{tag_name}'") from exc
        return {
            "name": str(getattr(release, "name", name)),
            "tag_name": str(getattr(release, "tag_name", tag_name)),
            "url": str(getattr(release, "_url", getattr(release, "url", ""))),
            "description": str(getattr(release, "description", description)),
        }
