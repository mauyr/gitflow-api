import unittest

from gitflow_api.domain.results import FeatureStartResult


class ResultTests(unittest.TestCase):
    def test_result_to_dict(self):
        result = FeatureStartResult(
            ok=True,
            action="feature_start",
            message="created",
            branch="feature/x",
            base_branch="staging",
            merge_request={"iid": 10},
        )
        self.assertEqual(
            result.to_dict(),
            {
                "ok": True,
                "action": "feature_start",
                "message": "created",
                "branch": "feature/x",
                "base_branch": "staging",
                "merge_request": {"iid": 10},
            },
        )
