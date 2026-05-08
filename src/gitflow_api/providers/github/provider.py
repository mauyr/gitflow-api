from __future__ import annotations

from gitflow_api.config.models import ProviderConfig
from gitflow_api.providers.github.client import GitHubApiClient
from gitflow_api.providers.github.pull_request_service import GitHubPullRequestService
from gitflow_api.providers.github.release_service import GitHubReleaseService


class GitHubProvider:
    def __init__(self, config: ProviderConfig, client: GitHubApiClient | None = None) -> None:
        self.client = client or GitHubApiClient(config.url, config.token)
        self.pull_requests = GitHubPullRequestService(self.client)
        self.releases = GitHubReleaseService(self.client)

    def find_merge_request(
        self,
        remote_url: str,
        source_branch: str,
        target_branch: str | None = None,
        state: str = "opened",
    ):
        return self.pull_requests.find(remote_url, source_branch, target_branch, state)

    def create_merge_request(
        self,
        remote_url: str,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str | None = None,
        labels: list[str] | None = None,
        draft: bool = True,
        remove_source_branch: bool = True,
    ):
        return self.pull_requests.create(
            remote_url,
            source_branch,
            target_branch,
            title,
            description,
            labels,
            draft,
            remove_source_branch,
        )

    def validate_merge_request_ready(
        self,
        remote_url: str,
        source_branch: str,
        target_branch: str | None = None,
    ):
        return self.pull_requests.validate_ready(remote_url, source_branch, target_branch)

    def merge_merge_request(
        self,
        remote_url: str,
        source_branch: str,
        target_branch: str | None = None,
    ):
        return self.pull_requests.merge(remote_url, source_branch, target_branch)

    def list_merge_requests(
        self,
        remote_url: str,
        target_branch: str | None = None,
        state: str = "merged",
    ):
        return self.pull_requests.list(remote_url, target_branch, state)

    def find_merge_request_by_commit_message(self, remote_url: str, commit_message: str):
        return self.pull_requests.find_by_commit_message(remote_url, commit_message)

    def create_release(
        self,
        remote_url: str,
        tag_name: str,
        name: str,
        description: str,
        ref: str | None = None,
    ):
        return self.releases.create(remote_url, tag_name, name, description, ref)
