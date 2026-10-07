import os
import tempfile
import unittest
from pathlib import Path

from gitflow_api.config.loader import load_config
from gitflow_api.domain.exceptions import ConfigError


class ConfigLoaderTests(unittest.TestCase):
    def test_loads_config_from_toml_and_env_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".gitflow.toml"
            config_path.write_text(
                """
[provider]
url = "https://gitlab.example.com"
token_env = "TEST_GITFLOW_TOKEN"

[branches]
develop = "develop"
""".strip(),
                encoding="utf-8",
            )
            os.environ["TEST_GITFLOW_TOKEN"] = "secret-token"
            try:
                config = load_config(config_path)
            finally:
                os.environ.pop("TEST_GITFLOW_TOKEN", None)

        self.assertEqual(config.provider.type, "gitlab")
        self.assertEqual(config.provider.url, "https://gitlab.example.com")
        self.assertEqual(config.provider.token, "secret-token")
        self.assertEqual(config.branches.main, "master")
        self.assertEqual(config.branches.develop, "develop")

    def test_loads_github_provider_with_default_token_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".gitflow.toml"
            config_path.write_text(
                """
[provider]
type = "github"
url = "https://api.github.com"
""".strip(),
                encoding="utf-8",
            )
            os.environ["GITHUB_TOKEN"] = "github-secret"
            try:
                config = load_config(config_path)
            finally:
                os.environ.pop("GITHUB_TOKEN", None)

        self.assertEqual(config.provider.type, "github")
        self.assertEqual(config.provider.token, "github-secret")

    def test_prefers_project_config_over_global_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_path = root / "repo"
            global_home = root / "xdg"
            repo_path.mkdir()
            global_config_path = global_home / "gitflow" / "gitflow.toml"
            global_config_path.parent.mkdir(parents=True)
            global_config_path.write_text(
                """
[provider]
type = "gitlab"
url = "https://gitlab.example.com"
token = "global-secret"
""".strip(),
                encoding="utf-8",
            )
            (repo_path / "gitflow.toml").write_text(
                """
[provider]
type = "github"
url = "https://github.com"
token = "project-secret"
""".strip(),
                encoding="utf-8",
            )

            previous = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = str(global_home)
            try:
                config = load_config(repo_path=repo_path)
            finally:
                if previous is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = previous

        self.assertEqual(config.provider.type, "github")
        self.assertEqual(config.provider.token, "project-secret")

    def test_project_config_can_add_deployment_profile_while_inheriting_global_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_path = root / "repo"
            global_home = root / "xdg"
            repo_path.mkdir()
            global_config_path = global_home / "gitflow" / "gitflow.toml"
            global_config_path.parent.mkdir(parents=True)
            global_config_path.write_text(
                """
[provider]
type = "github"
url = "https://api.github.com"
token = "global-secret"
""".strip(),
                encoding="utf-8",
            )
            (repo_path / "gitflow.toml").write_text(
                """
[launch]
release_name_template = "v{version}"

[[deploy.profiles]]
name = "production"
driver = "command"
command = ["deploy"]
""".strip(),
                encoding="utf-8",
            )
            previous = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = str(global_home)
            try:
                config = load_config(repo_path=repo_path)
            finally:
                if previous is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = previous

        self.assertEqual(config.provider.token, "global-secret")
        self.assertEqual(config.launch.release_name_template, "v{version}")
        self.assertEqual(config.deploy.profiles[0].name, "production")

    def test_prefers_gitflow_toml_over_hidden_project_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_path = Path(tmp)
            (repo_path / ".gitflow.toml").write_text(
                """
[provider]
type = "gitlab"
url = "https://gitlab.example.com"
token = "hidden-secret"
""".strip(),
                encoding="utf-8",
            )
            (repo_path / "gitflow.toml").write_text(
                """
[provider]
type = "github"
url = "https://github.com"
token = "plain-secret"
""".strip(),
                encoding="utf-8",
            )

            config = load_config(repo_path=repo_path)

        self.assertEqual(config.provider.type, "github")
        self.assertEqual(config.provider.token, "plain-secret")

    def test_falls_back_to_global_config_when_project_config_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo_path = root / "repo"
            global_home = root / "xdg"
            repo_path.mkdir()
            global_config_path = global_home / "gitflow" / "gitflow.toml"
            global_config_path.parent.mkdir(parents=True)
            global_config_path.write_text(
                """
[provider]
type = "github"
url = "https://github.com"
token = "global-secret"
""".strip(),
                encoding="utf-8",
            )

            previous = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = str(global_home)
            try:
                config = load_config(repo_path=repo_path)
            finally:
                if previous is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = previous

        self.assertEqual(config.provider.type, "github")
        self.assertEqual(config.provider.token, "global-secret")

    def test_rejects_unsupported_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".gitflow.toml"
            config_path.write_text(
                """
[provider]
type = "bitbucket"
url = "https://bitbucket.org"
token = "x"
""".strip(),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_config(config_path)

    def test_masks_invalid_token_env_in_missing_token_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "gitflow.toml"
            config_path.write_text(
                """
[provider]
type = "github"
url = "https://github.com"
token_env = "ghp-not-a-safe-env-name"
""".strip(),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError) as ctx:
                load_config(config_path)

        message = str(ctx.exception)
        self.assertIn("env:***MASKED***", message)
        self.assertNotIn("ghp-not-a-safe-env-name", message)

    def test_loads_launch_template_and_deployment_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "gitflow.toml"
            config_path.write_text(
                """
[provider]
type = "github"
url = "https://api.github.com"
token = "test-token"

[launch]
release_name_template = "v{version}"

[[deploy.profiles]]
name = "production"
driver = "command"
command = ["./scripts/deploy.sh", "{version}"]
timeout_seconds = 900
""".strip(),
                encoding="utf-8",
            )
            config = load_config(config_path)

        self.assertEqual(config.launch.release_name_template, "v{version}")
        self.assertEqual(len(config.deploy.profiles), 1)
        self.assertEqual(config.deploy.profiles[0].name, "production")
        self.assertEqual(config.deploy.profiles[0].options["timeout_seconds"], 900)

    def test_rejects_duplicate_deployment_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "gitflow.toml"
            config_path.write_text(
                """
[provider]
type = "github"
url = "https://api.github.com"
token = "test-token"

[[deploy.profiles]]
name = "production"
driver = "command"
command = ["true"]

[[deploy.profiles]]
name = "production"
driver = "command"
command = ["true"]
""".strip(),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "Duplicate deployment profile"):
                load_config(config_path)
