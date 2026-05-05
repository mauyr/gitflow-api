import unittest

from gitflow_api.git.url_parser import parse_remote_url


class UrlParserTests(unittest.TestCase):
    def test_parses_ssh_gitlab_remote(self):
        ref = parse_remote_url("git@gitlab.example.com:group/subgroup/project.git")
        self.assertEqual(ref.host, "gitlab.example.com")
        self.assertEqual(ref.namespace, "group/subgroup")
        self.assertEqual(ref.project, "project")
        self.assertEqual(ref.full_path, "group/subgroup/project")

    def test_parses_https_gitlab_remote(self):
        ref = parse_remote_url("https://gitlab.example.com/group/project.git")
        self.assertEqual(ref.host, "gitlab.example.com")
        self.assertEqual(ref.namespace, "group")
        self.assertEqual(ref.project, "project")
