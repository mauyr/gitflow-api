#!/usr/bin/env python
# encoding: utf-8
import configparser
import os
from subprocess import check_call

from git import Repo

from gitflow_api.config.properties import CONFIG_FILE


class GitHelper:
    global repo
    global path

    def __init__(self):
        self.data = []

        self.path = os.getcwd()
        self.repo = Repo(self.path)

    def get_current_url(self):
        return self.repo.remotes[0].url

    def get_current_branch(self):
        return self.repo.active_branch

    def create_new_branch_from(self, from_branch, new_branch):
        self.checkout_and_pull(from_branch)

        git_cmd = 'git checkout -b {}'
        check_call(git_cmd.format(new_branch), shell=True)

        self.push_branch(new_branch)

    def checkout_and_pull(self, branch):
        try:
            git_cmd = 'git checkout {}'
            check_call(git_cmd.format(branch), shell=True)

            git_cmd = 'git pull'
            check_call(git_cmd.format(branch), shell=True)
        except Exception as e:
            pass

    def commit_and_push_update_message(self, branch, version):
        self.checkout_and_pull(branch)

        try:
            git_cmd = 'git add .'
            check_call(git_cmd, shell=True)

            git_cmd = 'git commit -m "Update to next version {}"'
            check_call(git_cmd.format(version), shell=True)
        except Exception as e:
            print('Nothing to commmit. Skipping.')
            return

        self.push_branch(branch)

    def push_branch(self, branch):
        git_cmd = 'git push -u origin {}'
        check_call(git_cmd.format(branch), shell=True)

    def create_tag(self, tag, message):
        git_cmd = 'git tag -a "{}" -m "{}"'
        check_call(git_cmd.format(tag, message), shell=True)

        self.push_branch(tag)

    def check_conflicts(self, from_branch, to_branch):
        try:
            git_cmd = 'git merge --no-commit {}'
            check_call(git_cmd.format(from_branch), shell=True)

            self.push_branch(to_branch)
        except Exception:
            git_cmd = 'git reset HEAD --hard'
            check_call(git_cmd, shell=True)

            group_name, project_name = self.extract_group_and_project()

            raise RuntimeError('Project {} has conflict from branch {} into {}'.format(project_name, from_branch, to_branch))

    def extract_group_and_project(self):
        return GitHelper.extract_group_and_project_from_url(self.get_current_url())

    @staticmethod
    def extract_group_and_project_from_url(git_url):
        api_url = GitHelper.get_api_url_from_config()

        short_api_url = GitHelper.extract_url_without_protocol(api_url)
        short_git_url = GitHelper.extract_url_without_protocol(git_url)

        only_groups_and_project = short_git_url.replace(short_api_url, '')[1:].split('/')
        project = str(only_groups_and_project[len(only_groups_and_project)-1]).replace('.git', '')
        del only_groups_and_project[len(only_groups_and_project)-1]
        group = '/'.join(only_groups_and_project)
        return group, project

    @staticmethod
    def get_api_url_from_config():
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        api_url = str(config['API']['url']).lower()
        return api_url

    def get_git_cmd(self):
        return self.repo.git

    @staticmethod
    def extract_url_without_protocol(url):
        initial_pos = url.find('://')
        initial_pos = url.find('@')+1 if initial_pos == -1 else initial_pos+3
        return url[initial_pos:]
