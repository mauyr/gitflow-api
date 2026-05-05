from __future__ import annotations

from pathlib import Path

from gitflow_api.application.context import AppContext
from gitflow_api.config import load_config
from gitflow_api.domain.exceptions import UnsupportedProviderError
from gitflow_api.git.client import GitClient
from gitflow_api.providers.gitlab import GitLabProvider


def build_context(
    repo_path: str | None = None,
    config_path: str | None = None,
    *,
    git_client: GitClient | None = None,
    provider=None,
    provider_factory=None,
) -> AppContext:
    resolved_repo_path = str(Path(repo_path or ".").resolve())
    config = load_config(config_path)

    client = git_client or GitClient(resolved_repo_path)

    if provider is not None:
        resolved_provider = provider
    else:
        if config.provider.type != "gitlab":
            raise UnsupportedProviderError(
                f"Provider '{config.provider.type}' is not supported by this build."
            )
        if provider_factory is not None:
            resolved_provider = provider_factory(config.provider)
        else:
            resolved_provider = GitLabProvider(config.provider)

    return AppContext(
        config=config,
        git=client,
        provider=resolved_provider,
        repo_path=resolved_repo_path,
    )
