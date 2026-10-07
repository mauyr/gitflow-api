import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gitflow_api.cli.main import main
from gitflow_api.domain.results import ChangelogResult, DeployResult, FeatureStartResult, LaunchResult, ReleaseStartResult


class CliMainTests(unittest.TestCase):
    def test_version_json(self):
        with patch("builtins.print") as mock_print:
            exit_code = main(["--json", "version"])
        self.assertEqual(exit_code, 0)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertTrue(payload["ok"])
        self.assertIn("version", payload)

    def test_feature_start_json(self):
        fake_result = FeatureStartResult(
            ok=True,
            action="feature_start",
            message="done",
            branch="feature/demo",
            base_branch="staging",
            merge_request={"url": "https://gitlab.example.com/mr/1"},
        )
        with patch("gitflow_api.cli.main.build_context", return_value=object()), \
             patch("gitflow_api.cli.main.execute_feature_start", return_value=fake_result), \
             patch("builtins.print") as mock_print:
            exit_code = main(["--json", "feature", "start", "demo"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertEqual(payload["branch"], "feature/demo")
        self.assertEqual(payload["merge_request"]["url"], "https://gitlab.example.com/mr/1")

    def test_release_start_json(self):
        fake_result = ReleaseStartResult(
            ok=True,
            action="release_start",
            message="done",
            branch="release/1.2.3",
            version="1.2.3",
            merge_request={"url": "https://gitlab.example.com/mr/2"},
        )
        with patch("gitflow_api.cli.main.build_context", return_value=object()), \
             patch("gitflow_api.cli.main.execute_release_start", return_value=fake_result), \
             patch("builtins.print") as mock_print:
            exit_code = main(["--json", "release", "start", "1.2.3"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertEqual(payload["branch"], "release/1.2.3")

    def test_launch_json(self):
        fake_result = LaunchResult(
            ok=True,
            action="launch",
            message="done",
            version="1.2.3",
            tag="project-1.2.3",
            release={"url": "https://gitlab.example.com/release/1"},
            markdown="# notes",
        )
        with patch("gitflow_api.cli.main.build_context", return_value=object()), \
             patch("gitflow_api.cli.main.execute_launch", return_value=fake_result), \
             patch("builtins.print") as mock_print:
            exit_code = main(["--json", "launch", "1.2.3"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertEqual(payload["tag"], "project-1.2.3")
        self.assertEqual(payload["release"]["url"], "https://gitlab.example.com/release/1")

    def test_changelog_json(self):
        fake_result = ChangelogResult(
            ok=True,
            action="changelog",
            message="done",
            version="1.2.3",
            markdown="# notes",
            items=[{"title": "Story A"}],
        )
        with patch("gitflow_api.cli.main.build_context", return_value=object()), \
             patch("gitflow_api.cli.main.execute_changelog", return_value=fake_result), \
             patch("builtins.print") as mock_print:
            exit_code = main(["--json", "changelog", "1.2.3"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertEqual(payload["version"], "1.2.3")
        self.assertEqual(payload["items"][0]["title"], "Story A")

    def test_deploy_json(self):
        fake_result = DeployResult(
            ok=True,
            action="deploy",
            message="done",
            profile="production",
            version="1.2.3",
            tag="1.2.3",
            deployments=[{"status": "planned"}],
            dry_run=True,
        )
        with patch("gitflow_api.cli.main.build_context", return_value=object()), \
             patch("gitflow_api.cli.main.execute_deploy", return_value=fake_result), \
             patch("builtins.print") as mock_print:
            exit_code = main(["--json", "deploy", "production", "--version", "1.2.3", "--dry-run"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertEqual(payload["profile"], "production")
        self.assertTrue(payload["dry_run"])

    def test_config_check_masks_token_in_json_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "gitflow.toml"
            config_path.write_text(
                """
[provider]
type = "github"
url = "https://github.com"
token = "secret-token"
""".strip(),
                encoding="utf-8",
            )

            with patch("builtins.print") as mock_print:
                exit_code = main(["--json", "--config", str(config_path), "config-check"])

        self.assertEqual(exit_code, 0)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertEqual(payload["config"]["provider"]["token"], "***MASKED***")

    def test_install_project_config_non_interactive_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("builtins.print") as mock_print:
                exit_code = main([
                    "--json",
                    "--repo",
                    tmp,
                    "install",
                    "--scope",
                    "project",
                    "--provider",
                    "github",
                    "--token",
                    "secret-token",
                    "--non-interactive",
                ])

            config_path = Path(tmp) / "gitflow.toml"
            content = config_path.read_text(encoding="utf-8")

        self.assertEqual(exit_code, 0)
        payload = json.loads(mock_print.call_args.args[0])
        self.assertEqual(payload["scope"], "project")
        self.assertEqual(payload["provider"], "github")
        self.assertIn('token = "secret-token"', content)
        self.assertIn('feature_label = "feature"', content)
