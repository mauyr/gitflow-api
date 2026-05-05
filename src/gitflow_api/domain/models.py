from dataclasses import dataclass, field


@dataclass(frozen=True)
class BranchNames:
    main: str
    develop: str
    feature_prefix: str
    hotfix_prefix: str
    release_prefix: str


@dataclass(frozen=True)
class MergeRequestInfo:
    id: int
    iid: int
    title: str
    url: str
    source_branch: str
    target_branch: str
    state: str
    draft: bool
    merge_status: str | None = None
    labels: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ChangelogItem:
    title: str
    url: str
    type: str
    labels: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ReleaseNotes:
    version: str
    items: list[ChangelogItem] = field(default_factory=list)
