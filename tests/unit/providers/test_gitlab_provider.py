import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from gitflow_api.config.loader import load_config
from gitflow_api.domain.exceptions import MergeRequestNotFoundError, MergeRequestNotReadyError, ProviderError
from gitflow_api.providers.gitlab.mapper import GitLabMapper
from gitflow_api.providers.gitlab.provider import GitLabProvider
from gitflow_api.providers.gitlab.project_resolver import GitLabProjectResolver


class FakeMergeRequestManager:
    def __init__(self, merge_requests=None):
        self.merge_requests = merge_requests or []
        self.created_payload = None

    def list(self, state="opened", all=True):
        return [mr for mr in self.merge_requests if getattr(mr, "state", None) == state]

    def create(self, payload):
        self.created_payload = payload
        mr = SimpleNamespace(
            id=999,
            iid=77,
            title=payload["title"],
            web_url="https://gitlab.example.com/group/project/-/merge_requests/77",
            source_branch=payload["source_branch"],
            target_branch=payload["target_branch"],
            state="opened",
            draft=payload["title"].startswith("Draft:"),
            merge_status="can_be_merged",
            labels=payload.get("labels", []),
            discussion_locked=False,
            work_in_progress=False,
        )
        self.merge_requests.append(mr)
        return mr


class FakeReleaseManager:
    def __init__(self):
        self.created_payload = None

    def create(self, payload):
        self.created_payload = payload
        return SimpleNamespace(
            name=payload["name"],
            tag_name=payload["tag_name"],
            description=payload["description"],
            url=f"https://gitlab.example.com/group/project/-/releases/{payload['tag_name']}",
        )


class FakeProject:
    def __init__(self, merge_requests=None):
        self.mergerequests = FakeMergeRequestManager(merge_requests)
        self.releases = FakeReleaseManager()


class FakeProjectsApi:
    def __init__(self, project=None, should_fail=False):
        self.project = project or FakeProject()
        self.should_fail = should_fail
        self.requested = []

    def get(self, full_path):
        self.requested.append(full_path)
        if self.should_fail:
            raise RuntimeError("not found")
        return self.project


class FakeGitLabClient:
    def __init__(self, project=None, should_fail=False):
        self.projects = FakeProjectsApi(project=project, should_fail=should_fail)


class GitLabProviderTests(unittest.TestCase):
    def _load_provider_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".gitflow.toml"
            config_path.write_text(
                """
[provider]
url = "https://gitlab.example.com"
token = "secret"
""".strip(),
                encoding="utf-8",
            )
            return load_config(config_path).provider

    def test_project_resolver_uses_full_path(self):
        client = FakeGitLabClient()
        resolver = GitLabProjectResolver(client)
        resolver.resolve("git@gitlab.example.com:group/subgroup/project.git")
        self.assertEqual(client.projects.requested, ["group/subgroup/project"])

    def test_project_resolver_wraps_provider_error(self):
        resolver = GitLabProjectResolver(FakeGitLabClient(should_fail=True))
        with self.assertRaises(ProviderError):
            resolver.resolve("https://gitlab.example.com/group/project.git")

    def test_mapper_marks_draft_from_title(self):
        mapped = GitLabMapper.merge_request(
            SimpleNamespace(
                id=1,
                iid=2,
                title="Draft: test",
                web_url="u",
                source_branch="a",
                target_branch="b",
                state="opened",
                draft=False,
                work_in_progress=False,
                merge_status="can_be_merged",
                labels=["story"],
            )
        )
        self.assertTrue(mapped.draft)

    def test_create_merge_request_prefixes_draft_title(self):
        project = FakeProject()
        provider = GitLabProvider(self._load_provider_config(), client_factory=lambda *_: FakeGitLabClient(project))

        result = provider.create_merge_request(
            "https://gitlab.example.com/group/project.git",
            "feature/x",
            "staging",
            "my feature",
            labels=["story"],
            draft=True,
        )

        self.assertEqual(result.title, "Draft: my feature")
        self.assertEqual(project.mergerequests.created_payload["labels"], ["story"])

    def test_validate_merge_request_ready_rejects_draft(self):
        merge_request = SimpleNamespace(
            id=1,
            iid=10,
            title="Draft: work",
            web_url="u",
            source_branch="feature/x",
            target_branch="staging",
            state="opened",
            draft=True,
            merge_status="can_be_merged",
            discussion_locked=False,
            work_in_progress=False,
            labels=[],
        )
        project = FakeProject([merge_request])
        provider = GitLabProvider(self._load_provider_config(), client_factory=lambda *_: FakeGitLabClient(project))

        with self.assertRaises(MergeRequestNotReadyError):
            provider.validate_merge_request_ready(
                "https://gitlab.example.com/group/project.git",
                "feature/x",
                "staging",
            )

    def test_merge_merge_request_calls_merge(self):
        class MergeableMr(SimpleNamespace):
            def __init__(self):
                super().__init__(
                    id=1,
                    iid=10,
                    title="Ready",
                    web_url="u",
                    source_branch="feature/x",
                    target_branch="staging",
                    state="opened",
                    draft=False,
                    merge_status="can_be_merged",
                    discussion_locked=False,
                    work_in_progress=False,
                    labels=[],
                )
                self.merged = False

            def merge(self):
                self.merged = True

        merge_request = MergeableMr()
        project = FakeProject([merge_request])
        provider = GitLabProvider(self._load_provider_config(), client_factory=lambda *_: FakeGitLabClient(project))

        result = provider.merge_merge_request(
            "https://gitlab.example.com/group/project.git",
            "feature/x",
            "staging",
        )

        self.assertTrue(merge_request.merged)
        self.assertEqual(result.iid, 10)

    def test_merge_merge_request_raises_when_missing(self):
        provider = GitLabProvider(self._load_provider_config(), client_factory=lambda *_: FakeGitLabClient())
        with self.assertRaises(MergeRequestNotFoundError):
            provider.merge_merge_request(
                "https://gitlab.example.com/group/project.git",
                "feature/missing",
                "staging",
            )

    def test_create_release_maps_payload(self):
        project = FakeProject()
        provider = GitLabProvider(self._load_provider_config(), client_factory=lambda *_: FakeGitLabClient(project))
        result = provider.create_release(
            "https://gitlab.example.com/group/project.git",
            tag_name="project-1.2.3",
            name="project 1.2.3",
            description="notes",
            ref="master",
        )
        self.assertEqual(project.releases.created_payload["ref"], "master")
        self.assertEqual(result["tag_name"], "project-1.2.3")
