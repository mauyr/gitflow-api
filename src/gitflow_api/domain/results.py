from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class BaseResult:
    ok: bool
    action: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FeatureStartResult(BaseResult):
    branch: str
    base_branch: str
    merge_request: dict[str, Any] | None = None


@dataclass(frozen=True)
class FeatureFinishResult(BaseResult):
    branch: str
    merged_to: str
    merge_request: dict[str, Any] | None = None


@dataclass(frozen=True)
class ReleaseStartResult(BaseResult):
    branch: str
    version: str
    merge_request: dict[str, Any] | None = None


@dataclass(frozen=True)
class ReleaseFinishResult(BaseResult):
    branch: str
    merged_to: str
    merge_request: dict[str, Any] | None = None
    sync_merge_request: dict[str, Any] | None = None


@dataclass(frozen=True)
class LaunchResult(BaseResult):
    version: str
    tag: str
    release: dict[str, Any] | None = None
    markdown: str = ""


@dataclass(frozen=True)
class ChangelogResult(BaseResult):
    version: str
    markdown: str
    items: list[dict[str, Any]] = field(default_factory=list)
