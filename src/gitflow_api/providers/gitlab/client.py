from __future__ import annotations

from gitflow_api.domain.exceptions import ProviderError


class GitLabClientFactory:
    def __call__(self, base_url: str, private_token: str):
        try:
            import gitlab  # type: ignore
        except ModuleNotFoundError as exc:  # pragma: no cover - depends on runtime env
            raise ProviderError(
                "python-gitlab is not installed. Install project dependencies to use the GitLab provider."
            ) from exc

        return gitlab.Gitlab(base_url, private_token=private_token)
