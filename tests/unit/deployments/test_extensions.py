import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from gitflow_api.config.models import DeploymentProfileConfig
from gitflow_api.deployments.base import DeploymentEvent
from gitflow_api.deployments.command import CommandDeploymentExtension
from gitflow_api.deployments.digitalocean_apps import DigitalOceanAppsDeploymentExtension
from gitflow_api.deployments.registry import execute_profile
from gitflow_api.domain.exceptions import DeploymentError


class DeploymentExtensionTests(unittest.TestCase):
    def _event(self, profile, *, dry_run=True, repo_path="/tmp"):
        return DeploymentEvent(
            profile=profile,
            version="1.2.3",
            tag="1.2.3",
            repo_path=repo_path,
            remote_url="https://github.com/example/project.git",
            release={"url": "https://github.com/example/project/releases/tag/1.2.3"},
            dry_run=dry_run,
        )

    def test_command_driver_renders_release_context_without_executing_in_dry_run(self):
        profile = DeploymentProfileConfig(
            name="production",
            driver="command",
            options={"command": ["deploy", "--version", "{version}", "--tag", "{tag}"], "timeout_seconds": 60},
        )
        result = CommandDeploymentExtension().execute(self._event(profile))
        self.assertEqual(result.status, "planned")
        self.assertEqual(result.metadata["command"], ["deploy", "--version", "1.2.3", "--tag", "1.2.3"])

    def test_command_driver_rejects_unknown_template_variable(self):
        profile = DeploymentProfileConfig(
            name="production", driver="command", options={"command": ["deploy", "{unknown}"]}
        )
        with self.assertRaisesRegex(DeploymentError, "Unknown deployment template variable"):
            CommandDeploymentExtension().execute(self._event(profile))

    def test_digitalocean_driver_requires_release_components(self):
        profile = DeploymentProfileConfig(
            name="production", driver="digitalocean-app", options={"app_id": "app-123"}
        )
        with self.assertRaisesRegex(DeploymentError, "components list"):
            DigitalOceanAppsDeploymentExtension().execute(self._event(profile))

    def test_disabled_profile_cannot_execute(self):
        profile = DeploymentProfileConfig(
            name="production", driver="command", options={"enabled": False, "command": ["deploy"]}
        )
        with self.assertRaisesRegex(DeploymentError, "profile is disabled"):
            execute_profile(self._event(profile))

    def test_digitalocean_driver_dry_run_validates_components_and_does_not_execute_doctl(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "component"
            repo.mkdir()
            (repo / ".git").mkdir()
            profile = DeploymentProfileConfig(
                name="production",
                driver="digitalocean-app",
                options={
                    "app_id": "app-123",
                    "context": "production",
                    "components": [{"path": str(repo), "branch": "master", "tag": "{version}"}],
                },
            )
            with patch("gitflow_api.deployments.digitalocean_apps._run_git", side_effect=["", "", "commit-1", "commit-1"]), \
                 patch("gitflow_api.deployments.digitalocean_apps.subprocess.run") as run:
                result = DigitalOceanAppsDeploymentExtension().execute(self._event(profile, repo_path=str(repo)))

        self.assertEqual(result.status, "planned")
        self.assertEqual(result.metadata["app_id"], "app-123")
        self.assertIn("--context", result.metadata["command"])
        run.assert_not_called()
