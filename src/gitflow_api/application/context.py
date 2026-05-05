from dataclasses import dataclass

from gitflow_api.config.models import AppConfig
from gitflow_api.git.client import GitClient
from gitflow_api.providers.base import MergeRequestProvider


@dataclass(frozen=True)
class AppContext:
    config: AppConfig
    git: GitClient
    provider: MergeRequestProvider
    repo_path: str
