from __future__ import annotations

import json
from dataclasses import dataclass
from urllib import error, parse, request

from gitflow_api.domain.exceptions import ProviderError


@dataclass(frozen=True)
class GitHubResponse:
    status: int
    data: dict | list | None


class GitHubApiClient:
    def __init__(self, base_url: str, token: str) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.token = token.strip()

    def get(self, path: str, query: dict[str, object] | None = None) -> GitHubResponse:
        return self.request("GET", path, query=query)

    def post(self, path: str, payload: dict[str, object] | None = None) -> GitHubResponse:
        return self.request("POST", path, payload=payload)

    def put(self, path: str, payload: dict[str, object] | None = None) -> GitHubResponse:
        return self.request("PUT", path, payload=payload)

    def request(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, object] | None = None,
        payload: dict[str, object] | None = None,
    ) -> GitHubResponse:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if query:
            encoded = parse.urlencode({k: v for k, v in query.items() if v is not None})
            url = f"{url}?{encoded}"

        body = None
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "gitflow-api/0.4.0",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        req = request.Request(url, data=body, method=method, headers=headers)
        try:
            with request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw) if raw else None
                return GitHubResponse(status=getattr(resp, "status", 200), data=data)
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            details = ""
            if raw:
                try:
                    parsed = json.loads(raw)
                    details = str(parsed.get("message") or raw)
                except json.JSONDecodeError:
                    details = raw
            raise ProviderError(f"GitHub API error {exc.code}: {details or exc.reason}") from exc
        except error.URLError as exc:
            raise ProviderError(f"Failed to connect to GitHub API: {exc.reason}") from exc


def _normalize_base_url(url: str) -> str:
    parsed = parse.urlparse(url.strip())
    if not parsed.scheme or not parsed.netloc:
        raise ProviderError(f"Invalid GitHub provider url: {url}")

    host = parsed.netloc.lower()
    path = parsed.path.rstrip("/")

    if host in {"github.com", "www.github.com"}:
        return "https://api.github.com"
    if host == "api.github.com":
        return f"{parsed.scheme}://{parsed.netloc}{path}".rstrip("/")
    if path.endswith("/api/v3"):
        return f"{parsed.scheme}://{parsed.netloc}{path}".rstrip("/")
    if not path:
        return f"{parsed.scheme}://{parsed.netloc}/api/v3"
    return f"{parsed.scheme}://{parsed.netloc}{path}".rstrip("/")
