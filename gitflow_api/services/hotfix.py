#!/usr/bin/env python
# encoding: utf-8
import os

from gitflow_api.api.api_strategy import ApiStrategy
from gitflow_api.config.config import Config
from gitflow_api.utilities.git_helper import GitHelper


class Hotfix:

    CONFIG = Config()

    def hotfix_start(self, args):
        path = os.getcwd()
        api = ApiStrategy.get_instance(path)
        git = GitHelper()

        branch = self.CONFIG.hotfix_branch.format(args.branch)
        git.create_new_branch_from(self.CONFIG.master_branch, branch)

        title = args.title if args.title is not None else branch
        issue = args.issue if args.issue is not None else 0
        merge_request = api.get_merge_request_api().create_merge_request(git.get_current_url(), branch, 'WIP: ' + title,
                                                                         None,
                                                                         issue,
                                                                         self.CONFIG.master_branch, 'bug')
        print('Branch {} and mergeRequest {} as created'.format(branch, merge_request.iid))

    def hotfix_finish(self, args):
        path = os.getcwd()
        api = ApiStrategy.get_instance(path)
        git = GitHelper()

        branch = str(git.get_current_branch() if args.branch is None else args.branch)

        try:
            api.get_merge_request_api().validate_and_close_merge_request(git.get_current_url(), branch)
            git.get_git_cmd().checkout(self.CONFIG.master_branch)
            git.get_git_cmd().pull()

            print('Hotfix {} merged on {}'.format(branch, self.CONFIG.master_branch))

        except ValueError as e:
            print(str(e))
