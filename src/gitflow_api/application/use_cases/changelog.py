from __future__ import annotations

from dataclasses import dataclass

from gitflow_api.application.context import AppContext
from gitflow_api.domain.models import ChangelogItem
from gitflow_api.domain.results import ChangelogResult
from gitflow_api.git import parse_remote_url


@dataclass(frozen=True)
class ChangelogInput:
    version: str
    from_ref: str | None = None


def execute(data: ChangelogInput, ctx: AppContext) -> ChangelogResult:
    remote_url = ctx.git.current_remote_url()
    project_name = parse_remote_url(remote_url).project
    start_ref = data.from_ref or ctx.git.latest_tag()
    log = ctx.git.log(None if start_ref is None else f"{start_ref}..HEAD")

    items: list[ChangelogItem] = []
    seen: set[int] = set()
    for line in log.splitlines():
        merge_request = ctx.provider.find_merge_request_by_commit_message(remote_url, line)
        if merge_request is None or merge_request.id in seen:
            continue
        seen.add(merge_request.id)
        item_type = _classify_type(merge_request.labels, ctx)
        if item_type == "ignore":
            continue
        items.append(
            ChangelogItem(
                title=merge_request.title,
                url=merge_request.url,
                type=item_type,
                labels=merge_request.labels,
            )
        )

    markdown = _render_markdown(project_name, data.version, items)
    return ChangelogResult(
        ok=True,
        action="changelog",
        message="Changelog generated.",
        version=data.version,
        markdown=markdown,
        items=[item.__dict__ for item in items],
    )


def _classify_type(labels: list[str], ctx: AppContext) -> str:
    label_set = set(labels)
    if label_set & set(ctx.config.changelog.ignore_labels):
        return "ignore"
    if label_set & set(ctx.config.changelog.feature_labels):
        return "feature"
    if label_set & set(ctx.config.changelog.bug_labels):
        return "bug"
    if label_set & set(ctx.config.changelog.technical_labels):
        return "technical"
    return "other"


def _render_markdown(project_name: str, version: str, items: list[ChangelogItem]) -> str:
    groups = {
        "feature": "Improvements",
        "bug": "Bugs",
        "technical": "Technical Debts",
        "other": "Others",
    }
    lines = [f"# {project_name} {version}"]
    for group_key, heading in groups.items():
        group_items = [item for item in items if item.type == group_key]
        if not group_items:
            continue
        lines.append(f"\n## {heading}")
        for item in group_items:
            lines.append(f"- [{item.title}]({item.url})")
    return "\n".join(lines)
