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

    def test_rejects_unsupported_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / ".gitflow.toml"
            config_path.write_text(
                """
[provider]
type = "github"
url = "https://github.com"
token = "x"
""".strip(),
                encoding="utf-8",
            )
            with self.assertRaises(ConfigError):
                load_config(config_path)
