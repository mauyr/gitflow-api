import tempfile
import unittest
from pathlib import Path

from gitflow_api.config.loader import load_config
from gitflow_api.domain.exceptions import MergeRequestNotFoundError, MergeRequestNotReadyError
from gitflow_api.providers.github.provider import GitHubProvider


class FakeGitHubClient:
    def __init__(self):
        self.calls = []
        self.pull_requests = [
            {
                "id": 101,
                "number": 7,
                "title": "Feature X",
                "html_url": "https://github.com/mauyr/gitflow-api/pull/7",
                "state": "open",
                "draft": False,
                "mergeable": True,
                "mergeable_state": "clean",
                "merged": False,
                "merged_at": None,
                "head": {"ref": "feature/x"},
                "base": {"ref": "staging"},
                "labels": [{"name": "story"}],
            }
        ]
        self.next_number = 8
        self.last_created_payload = None
        self.last_labels_payload = None
        self.last_release_payload = None
        self.merged_numbers = []

    def get(self, path, query=None):
        self.calls.append(("GET", path, query, None))
        if path.endswith("/pulls"):
            items = list(self.pull_requests)
            if query:
                head = query.get("head")
                base = query.get("base")
                state = query.get("state")
                if head:
                    branch = str(head).split(":", 1)[1]
                    items = [item for item in items if item["head"]["ref"] == branch]
                if base:
                    items = [item for item in items if item["base"]["ref"] == base]
                if state == "open":
                    items = [item for item in items if item["state"] == "open"]
                elif state == "closed":
                    items = [item for item in items if item["state"] == "closed"]
            return type("Resp", (), {"data": items})()
        if "/pulls/" in path:
            number = int(path.rsplit("/", 1)[1])
            for item in self.pull_requests:
                if item["number"] == number:
                    return type("Resp", (), {"data": item})()
            return type("Resp", (), {"data": None})()
        raise AssertionError(f"unexpected GET path: {path}")

    def post(self, path, payload=None):
        self.calls.append(("POST", path, None, payload))
        if path.endswith("/pulls"):
            self.last_created_payload = payload
            created = {
                "id": 202,
                "number": self.next_number,
                "title": payload["title"],
                "html_url": f"https://github.com/mauyr/gitflow-api/pull/{self.next_number}",
                "state": "open",
                "draft": bool(payload.get("draft", False)),
                "mergeable": True,
                "mergeable_state": "clean",
                "merged": False,
                "merged_at": None,
                "head": {"ref": payload["head"]},
                "base": {"ref": payload["base"]},
                "labels": [],
            }
            self.pull_requests.append(created)
            self.next_number += 1
            return type("Resp", (), {"data": created})()
        if "/issues/" in path and path.endswith("/labels"):
            self.last_labels_payload = payload
            number = int(path.split("/issues/")[1].split("/", 1)[0])
            for item in self.pull_requests:
                if item["number"] == number:
                    item["labels"] = [{"name": label} for label in payload.get("labels", [])]
            return type("Resp", (), {"data": {"ok": True}})()
        if path.endswith("/releases"):
            self.last_release_payload = payload
            return type(
                "Resp",
                (),
                {
                    "data": {
                        "name": payload["name"],
                        "tag_name": payload["tag_name"],
                        "html_url": f"https://github.com/mauyr/gitflow-api/releases/tag/{payload['tag_name']}",
                        "body": payload["body"],
                    }
                },
            )()
        raise AssertionError(f"unexpected POST path: {path}")

    def put(self, path, payload=None):
        self.calls.append(("PUT", path, None, payload))
        if path.endswith("/merge"):
            number = int(path.split("/pulls/")[1].split("/", 1)[0])
            self.merged_numbers.append(number)
            for item in self.pull_requests:
                if item["number"] == number:
                    item["state"] = "closed"
                    item["merged"] = True
                    item["merged_at"] = "2026-01-01T00:00:00Z"
            return type("Resp", (), {"data": {"merged": True}})()
        raise AssertionError(f"unexpected PUT path: {path}")


class GitHubProviderTests(unittest.TestCase):
    def _load_provider_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".gitflow.toml"
            config_path.write_text(
                """
[provider]
type = "github"
url = "https://api.github.com"
token = "secret"
""".strip(),
                encoding="utf-8",
            )
            return load_config(config_path).provider

    def test_create_pull_request_and_labels(self):
        client = FakeGitHubClient()
        provider = GitHubProvider(self._load_provider_config(), client=client)

        result = provider.create_merge_request(
            "https://github.com/mauyr/gitflow-api.git",
            "feature/new-api",
            "staging",
            "New API",
            description="body",
            labels=["story"],
            draft=True,
        )

        self.assertEqual(result.iid, 8)
        self.assertTrue(result.draft)
        self.assertEqual(client.last_created_payload["head"], "feature/new-api")
        self.assertEqual(client.last_labels_payload["labels"], ["story"])

    def test_validate_ready_rejects_draft(self):
        client = FakeGitHubClient()
        client.pull_requests[0]["draft"] = True
        provider = GitHubProvider(self._load_provider_config(), client=client)

        with self.assertRaises(MergeRequestNotReadyError):
            provider.validate_merge_request_ready(
                "https://github.com/mauyr/gitflow-api.git",
                "feature/x",
                "staging",
            )

    def test_merge_pull_request(self):
        client = FakeGitHubClient()
        provider = GitHubProvider(self._load_provider_config(), client=client)

        result = provider.merge_merge_request(
            "https://github.com/mauyr/gitflow-api.git",
            "feature/x",
            "staging",
        )

        self.assertEqual(client.merged_numbers, [7])
        self.assertEqual(result.iid, 7)

    def test_merge_pull_request_raises_when_missing(self):
        client = FakeGitHubClient()
        provider = GitHubProvider(self._load_provider_config(), client=client)

        with self.assertRaises(MergeRequestNotFoundError):
            provider.merge_merge_request(
                "https://github.com/mauyr/gitflow-api.git",
                "feature/missing",
                "staging",
            )

    def test_find_pull_request_by_commit_message(self):
        client = FakeGitHubClient()
        provider = GitHubProvider(self._load_provider_config(), client=client)

        result = provider.find_merge_request_by_commit_message(
            "https://github.com/mauyr/gitflow-api.git",
            "feat: ship something (#7)",
        )

        self.assertIsNotNone(result)
        self.assertEqual(result.iid, 7)

    def test_create_release(self):
        client = FakeGitHubClient()
        provider = GitHubProvider(self._load_provider_config(), client=client)

        result = provider.create_release(
            "https://github.com/mauyr/gitflow-api.git",
            tag_name="gitflow-api-1.2.3",
            name="gitflow-api 1.2.3",
            description="notes",
            ref="master",
        )

        self.assertEqual(client.last_release_payload["target_commitish"], "master")
        self.assertEqual(result["tag_name"], "gitflow-api-1.2.3")
