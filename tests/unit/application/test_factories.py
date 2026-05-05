import os
import tempfile
import unittest
from pathlib import Path

from gitflow_api.application.factories import build_context


class DummyProvider:
    pass


class FactoryTests(unittest.TestCase):
    def test_build_context_uses_custom_provider_factory(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo_path = Path(tmp)
            (repo_path / ".gitflow.toml").write_text(
                """
[provider]
url = "https://gitlab.example.com"
token_env = "CTX_GITLAB_TOKEN"
""".strip(),
                encoding="utf-8",
            )
            old_cwd = Path.cwd()
            os.environ["CTX_GITLAB_TOKEN"] = "secret"
            try:
                os.chdir(repo_path)
                provider = DummyProvider()
                context = build_context(provider_factory=lambda provider_config: provider)
            finally:
                os.chdir(old_cwd)
                os.environ.pop("CTX_GITLAB_TOKEN", None)

        self.assertIs(context.provider, provider)
        self.assertEqual(context.config.provider.url, "https://gitlab.example.com")
        self.assertEqual(context.repo_path, str(repo_path.resolve()))
