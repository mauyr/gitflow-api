#!/usr/bin/env python

from gitlab.gitlab import Gitlab
from utilities.git_helper import GitHelper

from properties import *


class Hotfix:

    def hotfixStart(self, args):
        gitlab = Gitlab()
        git = GitHelper()

        branch = HOTFIX_BRANCH.format(args.branch)
        git.create_new_branch_from(MASTER_BRANCH, branch)

        title = args.title if args.title is not None else branch
        issue = args.issue if args.issue is not None else 0
        merge_request = gitlab.create_merge_request(git.get_current_url(), branch, 'WIP: ' + title, None,
                                                    issue,
                                                    MASTER_BRANCH, 'bug')
        print('Branch {} and mergeRequest {} as created'.format(branch, merge_request.iid))

    def hotfix_finish(self, args):
        gitlab = Gitlab()
        git = GitHelper()

        branch = str(git.get_current_branch() if args.branch is None else args.branch)

        try:
            gitlab.validate_and_close_merge_request(git.get_current_url(), branch)
            git.get_git_cmd().checkout(MASTER_BRANCH)
            git.get_git_cmd().pull()

            print('Hotfix {} merged on {}'.format(branch, MASTER_BRANCH))

        except ValueError as e:
            print(str(e))
