import unittest

from gitflow_api.application.context import AppContext
from gitflow_api.application.use_cases.changelog import ChangelogInput, execute as execute_changelog
from gitflow_api.application.use_cases.launch import LaunchInput, execute as execute_launch
from gitflow_api.application.use_cases.release_finish import ReleaseFinishInput, execute as execute_release_finish
from gitflow_api.application.use_cases.release_start import ReleaseStartInput, execute as execute_release_start
from gitflow_api.config.models import AppConfig, BehaviorConfig, BranchConfig, ChangelogConfig, MergeRequestConfig, ProviderConfig
from gitflow_api.domain.exceptions import ReleaseFlowError
from gitflow_api.domain.models import MergeRequestInfo


class FakeGit:
    def __init__(self, *, current_branch="release/1.2.3", remote_url="https://gitlab.example.com/group/project.git", latest_tag="project-1.2.2", log_output=""):
        self._current_branch = current_branch
        self._remote_url = remote_url
        self._latest_tag = latest_tag
        self._log_output = log_output
        self.actions = []

    def is_worktree_clean(self):
        return True

    def local_branch_exists(self, branch):
        return False

    def remote_branch_exists(self, branch):
        return False

    def create_branch(self, new_branch, from_branch):
        self.actions.append(("create_branch", new_branch, from_branch))

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

    def latest_tag(self):
        return self._latest_tag

    def log(self, revspec=None):
        self.actions.append(("log", revspec))
        return self._log_output

    def create_tag(self, tag, message=None):
        self.actions.append(("create_tag", tag, message))

    def push_tag(self, tag):
        self.actions.append(("push_tag", tag))


class FakeProvider:
    def __init__(self):
        self.calls = []
        self.feature_mr = MergeRequestInfo(
            id=10,
            iid=10,
            title="Story A",
            url="https://gitlab.example.com/group/project/-/merge_requests/10",
            source_branch="feature/story-a",
            target_branch="staging",
            state="merged",
            draft=False,
            merge_status="can_be_merged",
            labels=["story"],
        )
        self.release_mr = MergeRequestInfo(
            id=20,
            iid=20,
            title="Release 1.2.3",
            url="https://gitlab.example.com/group/project/-/merge_requests/20",
            source_branch="release/1.2.3",
            target_branch="master",
            state="opened",
            draft=False,
            merge_status="can_be_merged",
            labels=[],
        )

    def create_merge_request(self, **kwargs):
        self.calls.append(("create_merge_request", kwargs))
        if kwargs["source_branch"].startswith("release/") or kwargs["source_branch"] == "master":
            mr = self.release_mr if kwargs["source_branch"].startswith("release/") else MergeRequestInfo(
                id=21,
                iid=21,
                title=kwargs["title"],
                url="https://gitlab.example.com/group/project/-/merge_requests/21",
                source_branch=kwargs["source_branch"],
                target_branch=kwargs["target_branch"],
                state="opened",
                draft=False,
                merge_status="can_be_merged",
                labels=[],
            )
            return mr
        return self.feature_mr

    def validate_merge_request_ready(self, **kwargs):
        self.calls.append(("validate_merge_request_ready", kwargs))
        return self.release_mr

    def merge_merge_request(self, **kwargs):
        self.calls.append(("merge_merge_request", kwargs))
        return self.release_mr

    def find_merge_request_by_commit_message(self, remote_url, commit_message):
        self.calls.append(("find_merge_request_by_commit_message", commit_message))
        if "!10" in commit_message:
            return self.feature_mr
        return None

    def create_release(self, **kwargs):
        self.calls.append(("create_release", kwargs))
        return {
            "tag_name": kwargs["tag_name"],
            "name": kwargs["name"],
            "url": f"https://gitlab.example.com/group/project/-/releases/{kwargs['tag_name']}",
            "description": kwargs["description"],
        }


class ReleaseLaunchTests(unittest.TestCase):
    def _context(self, *, same_branches=False, git=None, provider=None):
        develop = "master" if same_branches else "staging"
        return AppContext(
            config=AppConfig(
                provider=ProviderConfig(type="gitlab", url="https://gitlab.example.com", token="secret"),
                branches=BranchConfig(
                    main="master",
                    develop=develop,
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
                    feature_labels=["story", "feature"],
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

    def test_release_start_requires_distinct_main_and_develop(self):
        with self.assertRaises(ReleaseFlowError):
            execute_release_start(ReleaseStartInput(version="1.2.3"), self._context(same_branches=True))

    def test_release_start_creates_branch_from_develop(self):
        git = FakeGit()
        provider = FakeProvider()
        result = execute_release_start(ReleaseStartInput(version="1.2.3"), self._context(git=git, provider=provider))
        self.assertEqual(result.branch, "release/1.2.3")
        self.assertIn(("create_branch", "release/1.2.3", "staging"), git.actions)
        self.assertEqual(provider.calls[0][1]["target_branch"], "master")

    def test_release_finish_merges_and_opens_sync_mr(self):
        git = FakeGit(current_branch="release/1.2.3")
        provider = FakeProvider()
        result = execute_release_finish(ReleaseFinishInput(), self._context(git=git, provider=provider))
        self.assertEqual(result.merged_to, "master")
        self.assertIsNotNone(result.sync_merge_request)
        self.assertIn(("checkout", "master"), git.actions)

    def test_changelog_uses_git_log_and_provider_lookup(self):
        git = FakeGit(log_output="commit a\n    See merge request group/project!10\n")
        provider = FakeProvider()
        result = execute_changelog(ChangelogInput(version="1.2.3"), self._context(git=git, provider=provider))
        self.assertEqual(len(result.items), 1)
        self.assertIn("Story A", result.markdown)
        self.assertIn(("log", "project-1.2.2..HEAD"), git.actions)

    def test_launch_creates_tag_and_release(self):
        git = FakeGit(log_output="commit a\n    See merge request group/project!10\n")
        provider = FakeProvider()
        result = execute_launch(LaunchInput(version="1.2.3"), self._context(git=git, provider=provider))
        self.assertEqual(result.tag, "project-1.2.3")
        self.assertIn(("create_tag", "project-1.2.3", "1.2.3"), git.actions)
        self.assertIn(("push_tag", "project-1.2.3"), git.actions)
        self.assertEqual(provider.calls[-1][0], "create_release")
