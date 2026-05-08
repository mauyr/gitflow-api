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
