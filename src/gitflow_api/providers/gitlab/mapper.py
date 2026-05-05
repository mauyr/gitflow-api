from __future__ import annotations

from gitflow_api.domain.models import MergeRequestInfo


class GitLabMapper:
    @staticmethod
    def merge_request(merge_request) -> MergeRequestInfo:
        return MergeRequestInfo(
            id=int(getattr(merge_request, "id", 0)),
            iid=int(getattr(merge_request, "iid", 0)),
            title=str(getattr(merge_request, "title", "")),
            url=str(getattr(merge_request, "web_url", "")),
            source_branch=str(getattr(merge_request, "source_branch", "")),
            target_branch=str(getattr(merge_request, "target_branch", "")),
            state=str(getattr(merge_request, "state", "")),
            draft=bool(
                getattr(merge_request, "draft", False)
                or getattr(merge_request, "work_in_progress", False)
                or str(getattr(merge_request, "title", "")).startswith(("Draft:", "WIP:"))
            ),
            merge_status=getattr(merge_request, "merge_status", None),
            labels=list(getattr(merge_request, "labels", []) or []),
        )
