from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:
    type: str
    url: str
    token: str


@dataclass(frozen=True)
class BranchConfig:
    main: str
    develop: str
    feature_prefix: str
    hotfix_prefix: str
    release_prefix: str


@dataclass(frozen=True)
class MergeRequestConfig:
    feature_label: str
    hotfix_label: str
    draft_prefix: str
    remove_source_branch: bool


@dataclass(frozen=True)
class ChangelogConfig:
    output_dir: str
    version_tag_pattern: str
    include_labels: bool
    feature_labels: list[str]
    bug_labels: list[str]
    technical_labels: list[str]
    ignore_labels: list[str]


@dataclass(frozen=True)
class BehaviorConfig:
    require_clean_worktree: bool
    auto_push: bool


@dataclass(frozen=True)
class AppConfig:
    provider: ProviderConfig
    branches: BranchConfig
    merge_request: MergeRequestConfig
    changelog: ChangelogConfig
    behavior: BehaviorConfig
