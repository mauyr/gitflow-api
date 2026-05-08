from __future__ import annotations

from gitflow_api.domain.models import MergeRequestInfo


class GitHubMapper:
    @staticmethod
    def pull_request(payload: dict) -> MergeRequestInfo:
        labels = [str(item.get("name", "")) for item in payload.get("labels", []) if item.get("name")]
        return MergeRequestInfo(
            id=int(payload.get("id", 0)),
            iid=int(payload.get("number", 0)),
            title=str(payload.get("title", "")),
            url=str(payload.get("html_url", "")),
            source_branch=str((payload.get("head") or {}).get("ref", "")),
            target_branch=str((payload.get("base") or {}).get("ref", "")),
            state=str(payload.get("state", "")),
            draft=bool(payload.get("draft", False)),
            merge_status=str(payload.get("mergeable_state")) if payload.get("mergeable_state") is not None else None,
            labels=labels,
        )
