from __future__ import annotations

import re

from gitflow_api.domain.exceptions import MergeRequestNotFoundError, MergeRequestNotReadyError
from gitflow_api.providers.gitlab.mapper import GitLabMapper
from gitflow_api.providers.gitlab.project_resolver import GitLabProjectResolver


class GitLabMergeRequestService:
    def __init__(self, gitlab_client) -> None:
        self.gitlab_client = gitlab_client
        self.project_resolver = GitLabProjectResolver(gitlab_client)

    def find(
        self,
        remote_url: str,
        source_branch: str,
        target_branch: str | None = None,
        state: str = "opened",
    ):
        project = self.project_resolver.resolve(remote_url)
        merge_requests = project.mergerequests.list(state=state, all=True)
        for merge_request in merge_requests:
            if str(getattr(merge_request, "source_branch", "")) != source_branch:
                continue
            if target_branch is not None and str(getattr(merge_request, "target_branch", "")) != target_branch:
                continue
            return GitLabMapper.merge_request(merge_request)
        return None

    def create(
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
        existing = self.find(remote_url, source_branch, target_branch, state="opened")
        if existing is not None:
            return existing

        project = self.project_resolver.resolve(remote_url)
        full_title = title
        if draft and not title.startswith(("Draft:", "WIP:")):
            full_title = f"Draft: {title}"

        payload = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": full_title,
            "description": description or "",
            "labels": labels or [],
            "remove_source_branch": remove_source_branch,
        }
        merge_request = project.mergerequests.create(payload)
        return GitLabMapper.merge_request(merge_request)

    def validate_ready(self, remote_url: str, source_branch: str, target_branch: str | None = None):
        project = self.project_resolver.resolve(remote_url)
        merge_request = self._find_raw(project, source_branch, target_branch)
        if merge_request is None:
            raise MergeRequestNotFoundError(f"Merge request not found for branch '{source_branch}'")

        title = str(getattr(merge_request, "title", ""))
        is_draft = bool(getattr(merge_request, "draft", False) or getattr(merge_request, "work_in_progress", False))
        if is_draft or title.startswith(("Draft:", "WIP:")):
            raise MergeRequestNotReadyError(f"Merge request {merge_request.iid} is still draft/WIP")

        if bool(getattr(merge_request, "discussion_locked", False)):
            raise MergeRequestNotReadyError(f"Merge request {merge_request.iid} has unresolved discussions")

        merge_status = str(getattr(merge_request, "merge_status", ""))
        if merge_status and merge_status not in {"can_be_merged", "mergeable"}:
            raise MergeRequestNotReadyError(
                f"Merge request {merge_request.iid} is not ready for merge: {merge_status}"
            )

        return GitLabMapper.merge_request(merge_request)

    def merge(self, remote_url: str, source_branch: str, target_branch: str | None = None):
        project = self.project_resolver.resolve(remote_url)
        merge_request = self._find_raw(project, source_branch, target_branch)
        if merge_request is None:
            raise MergeRequestNotFoundError(f"Merge request not found for branch '{source_branch}'")

        self.validate_ready(remote_url, source_branch, target_branch)
        merge_request.merge()
        return GitLabMapper.merge_request(merge_request)

    def list(self, remote_url: str, target_branch: str | None = None, state: str = "merged"):
        project = self.project_resolver.resolve(remote_url)
        items = []
        for merge_request in project.mergerequests.list(state=state, all=True):
            if target_branch is not None and str(getattr(merge_request, "target_branch", "")) != target_branch:
                continue
            items.append(GitLabMapper.merge_request(merge_request))
        return items

    def find_by_commit_message(self, remote_url: str, commit_message: str):
        match = re.search(r"!([0-9]+)", commit_message)
        if match is None:
            return None
        project = self.project_resolver.resolve(remote_url)
        merge_request = project.mergerequests.get(int(match.group(1)))
        return GitLabMapper.merge_request(merge_request)

    def _find_raw(self, project, source_branch: str, target_branch: str | None = None):
        merge_requests = project.mergerequests.list(state="opened", all=True)
        for merge_request in merge_requests:
            if str(getattr(merge_request, "source_branch", "")) != source_branch:
                continue
            if target_branch is not None and str(getattr(merge_request, "target_branch", "")) != target_branch:
                continue
            return merge_request
        return None
