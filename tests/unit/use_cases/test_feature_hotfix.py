import unittest
from dataclasses import dataclass

from gitflow_api.application.context import AppContext
from gitflow_api.application.use_cases.feature_finish import FeatureFinishInput, execute as execute_feature_finish
from gitflow_api.application.use_cases.feature_start import FeatureStartInput, execute as execute_feature_start
from gitflow_api.application.use_cases.hotfix_finish import HotfixFinishInput, execute as execute_hotfix_finish
from gitflow_api.application.use_cases.hotfix_start import HotfixStartInput, execute as execute_hotfix_start
from gitflow_api.config.models import AppConfig, BehaviorConfig, BranchConfig, ChangelogConfig, MergeRequestConfig, ProviderConfig
from gitflow_api.domain.exceptions import BranchAlreadyExistsError, WorkingTreeNotCleanError
from gitflow_api.domain.models import MergeRequestInfo


class FakeGit:
    def __init__(self, *, clean=True, current_branch="feature/demo", remote_url="https://gitlab.example.com/group/project.git", local_exists=None, remote_exists=None):
        self.clean = clean
        self._current_branch = current_branch
        self._remote_url = remote_url
        self.local_exists = set(local_exists or [])
        self.remote_exists = set(remote_exists or [])
        self.actions = []

    def is_worktree_clean(self):
        return self.clean

    def local_branch_exists(self, branch):
        return branch in self.local_exists

    def remote_branch_exists(self, branch):
        return branch in self.remote_exists

    def create_branch(self, new_branch, from_branch):
        self.actions.append(("create_branch", new_branch, from_branch))
        self.local_exists.add(new_branch)

    def push(self, branch, set_upstream=True):
        self.actions.append(("push", branch, set_upstream))

    def current_remote_url(self):
        return self._remote_url

    def current_branch(self):
        return self._current_branch

    def checkout(self, branch):
        self.actions.append(("checkout", branch))
        self._current_branch = branch

    def pull(self, branch=None):
        self.actions.append(("pull", branch))


class FakeProvider:
    def __init__(self):
        self.calls = []
        self.merge_request = MergeRequestInfo(
            id=1,
            iid=2,
            title="Draft: demo",
            url="https://gitlab.example.com/group/project/-/merge_requests/2",
            source_branch="feature/demo",
            target_branch="staging",
            state="opened",
            draft=True,
            merge_status="can_be_merged",
            labels=["story"],
        )

    def create_merge_request(self, **kwargs):
        self.calls.append(("create_merge_request", kwargs))
        return self.merge_request

    def validate_merge_request_ready(self, **kwargs):
        self.calls.append(("validate_merge_request_ready", kwargs))
        return self.merge_request

    def merge_merge_request(self, **kwargs):
        self.calls.append(("merge_merge_request", kwargs))
        return self.merge_request


class UseCaseTests(unittest.TestCase):
    def _context(self, git=None, provider=None):
        return AppContext(
            config=AppConfig(
                provider=ProviderConfig(type="gitlab", url="https://gitlab.example.com", token="secret"),
                branches=BranchConfig(
                    main="master",
                    develop="staging",
                    feature_prefix="feature/",
                    hotfix_prefix="hotfix/",
                    release_prefix="release/",
                ),
                merge_request=MergeRequestConfig(
                    feature_label="story",
                    hotfix_label="bug",
                    draft_prefix="Draft: ",
                    remove_source_branch=True,
                ),
                changelog=ChangelogConfig(
                    output_dir="release_notes",
                    version_tag_pattern="{project}-{version}",
                    include_labels=True,
                    feature_labels=["story"],
                    bug_labels=["bug"],
                    technical_labels=["technical debt"],
                    ignore_labels=["ignore"],
                ),
                behavior=BehaviorConfig(require_clean_worktree=True, auto_push=True),
            ),
            git=git or FakeGit(),
            provider=provider or FakeProvider(),
            repo_path="/tmp/repo",
        )

    def test_feature_start_creates_branch_push_and_mr(self):
        git = FakeGit(clean=True)
        provider = FakeProvider()
        result = execute_feature_start(FeatureStartInput(name="demo", title="My Feature", draft=True), self._context(git, provider))

        self.assertEqual(result.branch, "feature/demo")
        self.assertIn(("create_branch", "feature/demo", "staging"), git.actions)
        self.assertIn(("push", "feature/demo", True), git.actions)
        self.assertEqual(provider.calls[0][0], "create_merge_request")
        self.assertEqual(provider.calls[0][1]["target_branch"], "staging")

    def test_feature_start_rejects_dirty_worktree(self):
        with self.assertRaises(WorkingTreeNotCleanError):
            execute_feature_start(FeatureStartInput(name="demo"), self._context(git=FakeGit(clean=False)))

    def test_feature_start_rejects_existing_branch(self):
        with self.assertRaises(BranchAlreadyExistsError):
            execute_feature_start(FeatureStartInput(name="demo"), self._context(git=FakeGit(local_exists={"feature/demo"})))

    def test_feature_finish_validates_merges_and_syncs_branch(self):
        git = FakeGit(current_branch="feature/demo")
        provider = FakeProvider()
        result = execute_feature_finish(FeatureFinishInput(), self._context(git, provider))

        self.assertEqual(result.merged_to, "staging")
        self.assertEqual(provider.calls[0][0], "validate_merge_request_ready")
        self.assertEqual(provider.calls[1][0], "merge_merge_request")
        self.assertIn(("checkout", "staging"), git.actions)
        self.assertIn(("pull", "staging"), git.actions)

    def test_hotfix_start_targets_main(self):
        git = FakeGit(clean=True)
        provider = FakeProvider()
        result = execute_hotfix_start(HotfixStartInput(name="urgent", title="Urgent Fix", draft=False), self._context(git, provider))

        self.assertEqual(result.branch, "hotfix/urgent")
        self.assertIn(("create_branch", "hotfix/urgent", "master"), git.actions)
        self.assertEqual(provider.calls[0][1]["target_branch"], "master")
        self.assertEqual(provider.calls[0][1]["labels"], ["bug"])

    def test_hotfix_finish_targets_main(self):
        git = FakeGit(current_branch="hotfix/urgent")
        provider = FakeProvider()
        result = execute_hotfix_finish(HotfixFinishInput(), self._context(git, provider))

        self.assertEqual(result.merged_to, "master")
        self.assertIn(("checkout", "master"), git.actions)
        self.assertIn(("pull", "master"), git.actions)
