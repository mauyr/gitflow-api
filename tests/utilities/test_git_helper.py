#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase
from gitflow.utilities.git_helper import GitHelper


class TestGitHelper(TestCase):
    def test_extract_group_and_project_from_url_ssh(self):
        url = "git@git.domain.com.br:group/project.git"
        group, project = GitHelper.extract_group_and_project_from_url(url)
        self.assertEqual(group, 'group')
        self.assertEqual(project, 'project')

    def test_extract_group_and_project_from_url_http(self):
        url = "https://git.domain.com.br/group/project.git"
        group, project = GitHelper.extract_group_and_project_from_url(url)
        self.assertEqual(group, 'group')
        self.assertEqual(project, 'project')
