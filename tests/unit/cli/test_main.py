import json
import unittest
from unittest.mock import patch

from gitflow_api.cli.main import main
from gitflow_api.domain.results import FeatureStartResult


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
