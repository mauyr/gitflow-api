#!/usr/bin/env python

import os
from subprocess import check_call

from git import Repo


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

        git_cmd = 'git push -u origin {}'
        check_call(git_cmd.format(new_branch), shell=True)

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

        git_cmd = 'git push -u origin {}'
        check_call(git_cmd.format(branch), shell=True)

    def create_tag(self, tag, message):
        git_cmd = 'git tag -a {} -m "{}"'
        check_call(git_cmd.format(tag, message), shell=True)

        git_cmd = 'git push -u origin {}'
        check_call(git_cmd.format(tag), shell=True)

    def check_conflicts(self, branch):
        try:
            git_cmd = 'git merge --no-commit {}'
            check_call(git_cmd.format(branch), shell=True)
        except Exception:
            git_cmd = 'git reset HEAD --hard'
            check_call(git_cmd, shell=True)

            raise RuntimeError('Conflict with branch {}'.format(branch))

    def extract_group_and_project(self):
        return GitHelper.extract_group_and_project_from_url(self.get_current_url())

    @staticmethod
    def extract_group_and_project_from_url(git_url):
        if git_url.find('http') >= 0:
            url = git_url.split('/')
            group_name = str(url[len(url) - 2])
            project_name = str(url[len(url) - 1]).replace('.git', '')
            return group_name, project_name
        else:
            url = git_url.split('/')
            group_name = str(url[0][url[0].rfind(':') + 1:])
            project_name = str(url[1]).replace('.git', '')
            return group_name, project_name

    def get_git_cmd(self):
        return self.repo.git
