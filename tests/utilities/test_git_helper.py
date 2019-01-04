#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase
from unittest.mock import patch
from gitflow_api.utilities.git_helper import GitHelper


class TestGitHelper(TestCase):

    @staticmethod
    def fake_get_api_config_from_config():
        return 'https://git.domain.com.br'

    @patch.object(GitHelper, 'get_api_url_from_config', fake_get_api_config_from_config)
    def test_extract_group_and_project_from_url_ssh(self):
        url = "git@git.domain.com.br:group/project.git"
        group, project = GitHelper.extract_group_and_project_from_url(url)
        self.assertEqual(group, 'group')
        self.assertEqual(project, 'project')

    @patch.object(GitHelper, 'get_api_url_from_config', fake_get_api_config_from_config)
    def test_extract_group_and_project_from_url_http(self):
        url = "https://git.domain.com.br/group/project.git"
        group, project = GitHelper.extract_group_and_project_from_url(url)
        self.assertEqual(group, 'group')
        self.assertEqual(project, 'project')

    @patch.object(GitHelper, 'get_api_url_from_config', fake_get_api_config_from_config)
    def test_extract_group_and_subgroup_and_project_from_url_http(self):
        url = "https://git.domain.com.br/group/subgroup/project.git"
        group, project = GitHelper.extract_group_and_project_from_url(url)
        self.assertEqual(group, 'group/subgroup')
        self.assertEqual(project, 'project')

    @patch.object(GitHelper, 'get_api_url_from_config', fake_get_api_config_from_config)
    def test_extract_group_and_subgroup_and_project_from_url_ssh(self):
        url = "git@git.domain.com.br:group/subgroup/project.git"
        group, project = GitHelper.extract_group_and_project_from_url(url)
        self.assertEqual(group, 'group/subgroup')
        self.assertEqual(project, 'project')
