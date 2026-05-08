from __future__ import annotations

from gitflow_api.domain.exceptions import ProviderError
from gitflow_api.providers.github.project_resolver import GitHubProjectResolver


class GitHubReleaseService:
    def __init__(self, client) -> None:
        self.client = client
        self.project_resolver = GitHubProjectResolver()

    def create(self, remote_url: str, tag_name: str, name: str, description: str, ref: str | None = None) -> dict:
        owner, repo, _ = self.project_resolver.resolve(remote_url)
        payload = {
            "tag_name": tag_name,
            "name": name,
            "body": description,
            "draft": False,
            "prerelease": False,
        }
        if ref:
            payload["target_commitish"] = ref
        try:
            release = self.client.post(f"/repos/{owner}/{repo}/releases", payload=payload).data
        except ProviderError as exc:
            raise ProviderError(f"Failed to create GitHub release for tag '{tag_name}'") from exc
        if not isinstance(release, dict):
            raise ProviderError("GitHub API returned an invalid release payload")
        return {
            "name": str(release.get("name", name)),
            "tag_name": str(release.get("tag_name", tag_name)),
            "url": str(release.get("html_url", "")),
            "description": str(release.get("body", description)),
        }
