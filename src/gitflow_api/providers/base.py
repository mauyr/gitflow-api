from __future__ import annotations

from typing import Protocol

from gitflow_api.domain.models import MergeRequestInfo


class MergeRequestProvider(Protocol):
    def find_merge_request(
        self,
        remote_url: str,
        source_branch: str,
        target_branch: str | None = None,
        state: str = "opened",
    ) -> MergeRequestInfo | None:
        ...

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
    ) -> MergeRequestInfo:
        ...

    def validate_merge_request_ready(
        self,
        remote_url: str,
        source_branch: str,
        target_branch: str | None = None,
    ) -> MergeRequestInfo:
        ...

    def merge_merge_request(
        self,
        remote_url: str,
        source_branch: str,
        target_branch: str | None = None,
    ) -> MergeRequestInfo:
        ...

    def list_merge_requests(
        self,
        remote_url: str,
        target_branch: str | None = None,
        state: str = "merged",
    ) -> list[MergeRequestInfo]:
        ...
