#!/usr/bin/env python
# encoding: utf-8
import os

from gitflow_api.api.api_strategy import ApiStrategy
from gitflow_api.config.config import Config
from gitflow_api.utilities.git_helper import GitHelper


class Feature:

    config = None

    def feature_start(self, args):
        path = os.getcwd()
        api = ApiStrategy.get_instance(path)
        git = GitHelper()

        branch = self._get_config().feature_branch.format(args.branch)
        git.create_new_branch_from(self._get_config().staging_branch, branch)

        title = args.title if args.title is not None else branch
        issue = args.issue if args.issue is not None else 0
        merge_request = api.get_merge_request_api().create_merge_request(git.get_current_url(), branch, 'WIP: ' + title,
                                                                         '', issue,
                                                                         self._get_config().staging_branch, 'story')
        print('Branch {} and merge_request {} as created'.format(branch, merge_request.iid))

    def feature_finish(self, args):
        path = os.getcwd()
        api = ApiStrategy.get_instance(path)
        git = GitHelper()

        branch = str(git.get_current_branch() if args.branch is None else args.branch)

        try:
            api.get_merge_request_api().validate_and_close_merge_request(git.get_current_url(), branch)
            git.get_git_cmd().checkout(self._get_config().staging_branch)
            git.get_git_cmd().pull()

            print('Feature {} merged on {}'.format(branch, self._get_config().feature_branch))

        except ValueError as e:
            print(str(e))


    def _get_config(self):
        if self.config is None:
            self.config = Config()
    
        return self.config