from __future__ import annotations

from urllib.parse import urlparse

from gitflow_api.domain.exceptions import RepositoryError
from gitflow_api.git.models import RemoteProjectRef


def parse_remote_url(url: str) -> RemoteProjectRef:
    normalized = url.strip()
    if not normalized:
        raise RepositoryError("Remote URL is empty")

    if normalized.startswith("git@") and ":" in normalized:
        host_part, path_part = normalized[4:].split(":", 1)
        return _build_ref(host_part, path_part)

    parsed = urlparse(normalized)
    if parsed.scheme and parsed.netloc:
        return _build_ref(parsed.netloc, parsed.path.lstrip("/"))

    raise RepositoryError(f"Unsupported remote URL format: {url}")


def _build_ref(host: str, raw_path: str) -> RemoteProjectRef:
    cleaned = raw_path.removesuffix(".git").strip("/")
    parts = [part for part in cleaned.split("/") if part]
    if len(parts) < 2:
        raise RepositoryError(f"Remote URL path does not include namespace/project: {raw_path}")

    project = parts[-1]
    namespace = "/".join(parts[:-1])
    return RemoteProjectRef(host=host, namespace=namespace, project=project, full_path=cleaned)
