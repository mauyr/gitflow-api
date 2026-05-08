from __future__ import annotations

import re

from gitflow_api.domain.exceptions import MergeRequestNotFoundError, MergeRequestNotReadyError, ProviderError
from gitflow_api.providers.github.mapper import GitHubMapper
from gitflow_api.providers.github.project_resolver import GitHubProjectResolver


class GitHubPullRequestService:
    def __init__(self, client) -> None:
        self.client = client
        self.project_resolver = GitHubProjectResolver()

    def find(
        self,
        remote_url: str,
        source_branch: str,
        target_branch: str | None = None,
        state: str = "opened",
    ):
        owner, repo, _ = self.project_resolver.resolve(remote_url)
        github_state = _map_state(state)
        params = {
            "state": github_state,
            "head": f"{owner}:{source_branch}",
            "per_page": 100,
        }
        if target_branch is not None:
            params["base"] = target_branch
        response = self.client.get(f"/repos/{owner}/{repo}/pulls", query=params)
        items = response.data or []
        if not isinstance(items, list):
            return None
        for pull_request in items:
            if str(((pull_request.get("head") or {}).get("ref", ""))) != source_branch:
                continue
            if target_branch is not None and str(((pull_request.get("base") or {}).get("ref", ""))) != target_branch:
                continue
            if state == "merged" and not pull_request.get("merged_at"):
                continue
            return GitHubMapper.pull_request(pull_request)
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
        del remove_source_branch
        existing = self.find(remote_url, source_branch, target_branch, state="opened")
        if existing is not None:
            return existing

        owner, repo, _ = self.project_resolver.resolve(remote_url)
        payload = {
            "title": title,
            "body": description or "",
            "head": source_branch,
            "base": target_branch,
            "draft": draft,
        }
        created = self.client.post(f"/repos/{owner}/{repo}/pulls", payload=payload).data
        if not isinstance(created, dict):
            raise ProviderError("GitHub API returned an invalid pull request payload")
        number = int(created.get("number", 0))
        if labels:
            self.client.post(f"/repos/{owner}/{repo}/issues/{number}/labels", payload={"labels": labels})
            created = self.client.get(f"/repos/{owner}/{repo}/pulls/{number}").data
        return GitHubMapper.pull_request(created)

    def validate_ready(self, remote_url: str, source_branch: str, target_branch: str | None = None):
        payload = self._find_raw(remote_url, source_branch, target_branch)
        if payload is None:
            raise MergeRequestNotFoundError(f"Pull request not found for branch '{source_branch}'")

        number = int(payload.get("number", 0))
        if payload.get("state") != "open":
            raise MergeRequestNotReadyError(f"Pull request #{number} is not open")
        if bool(payload.get("draft", False)):
            raise MergeRequestNotReadyError(f"Pull request #{number} is still draft")
        if bool(payload.get("merged", False)):
            raise MergeRequestNotReadyError(f"Pull request #{number} is already merged")
        mergeable = payload.get("mergeable")
        mergeable_state = str(payload.get("mergeable_state", ""))
        if mergeable is False:
            raise MergeRequestNotReadyError(
                f"Pull request #{number} is not mergeable: {mergeable_state or 'mergeable=false'}"
            )
        if mergeable_state in {"dirty", "blocked", "draft", "unknown"}:
            raise MergeRequestNotReadyError(f"Pull request #{number} is not ready for merge: {mergeable_state}")
        return GitHubMapper.pull_request(payload)

    def merge(self, remote_url: str, source_branch: str, target_branch: str | None = None):
        payload = self._find_raw(remote_url, source_branch, target_branch)
        if payload is None:
            raise MergeRequestNotFoundError(f"Pull request not found for branch '{source_branch}'")

        ready = self.validate_ready(remote_url, source_branch, target_branch)
        owner, repo, _ = self.project_resolver.resolve(remote_url)
        number = int(payload.get("number", 0))
        merge_payload = {"merge_method": "merge"}
        self.client.put(f"/repos/{owner}/{repo}/pulls/{number}/merge", payload=merge_payload)
        merged = self.client.get(f"/repos/{owner}/{repo}/pulls/{number}").data
        if not isinstance(merged, dict):
            return ready
        return GitHubMapper.pull_request(merged)

    def list(self, remote_url: str, target_branch: str | None = None, state: str = "merged"):
        owner, repo, _ = self.project_resolver.resolve(remote_url)
        github_state = "closed" if state == "merged" else _map_state(state)
        params = {"state": github_state, "per_page": 100}
        if target_branch is not None:
            params["base"] = target_branch
        response = self.client.get(f"/repos/{owner}/{repo}/pulls", query=params)
        items = response.data or []
        results = []
        if not isinstance(items, list):
            return results
        for pull_request in items:
            if target_branch is not None and str(((pull_request.get("base") or {}).get("ref", ""))) != target_branch:
                continue
            if state == "merged" and not pull_request.get("merged_at"):
                continue
            results.append(GitHubMapper.pull_request(pull_request))
        return results

    def find_by_commit_message(self, remote_url: str, commit_message: str):
        number = _extract_pull_request_number(commit_message)
        if number is None:
            return None
        owner, repo, _ = self.project_resolver.resolve(remote_url)
        payload = self.client.get(f"/repos/{owner}/{repo}/pulls/{number}").data
        if not isinstance(payload, dict):
            return None
        return GitHubMapper.pull_request(payload)

    def _find_raw(self, remote_url: str, source_branch: str, target_branch: str | None = None):
        owner, repo, _ = self.project_resolver.resolve(remote_url)
        params = {
            "state": "open",
            "head": f"{owner}:{source_branch}",
            "per_page": 100,
        }
        if target_branch is not None:
            params["base"] = target_branch
        response = self.client.get(f"/repos/{owner}/{repo}/pulls", query=params)
        items = response.data or []
        if not isinstance(items, list):
            return None
        for pull_request in items:
            if str(((pull_request.get("head") or {}).get("ref", ""))) != source_branch:
                continue
            if target_branch is not None and str(((pull_request.get("base") or {}).get("ref", ""))) != target_branch:
                continue
            return self.client.get(f"/repos/{owner}/{repo}/pulls/{int(pull_request.get('number', 0))}").data
        return None


def _extract_pull_request_number(commit_message: str) -> int | None:
    patterns = [
        r"Merge pull request #(\d+)",
        r"\(#(\d+)\)",
        r"pull request #(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, commit_message, flags=re.IGNORECASE)
        if match is not None:
            return int(match.group(1))
    return None


def _map_state(state: str) -> str:
    normalized = state.strip().lower()
    if normalized in {"opened", "open"}:
        return "open"
    if normalized in {"closed", "close"}:
        return "closed"
    if normalized == "all":
        return "all"
    if normalized == "merged":
        return "closed"
    return normalized
