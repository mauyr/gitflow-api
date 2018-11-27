#!/usr/bin/env python

import os
from gitflowLibs.GitlabHelper import GitlabHelper
from gitflowLibs.GitHelper import GitHelper
from subprocess import call, check_call

from gitflowLibs.version_management import VersionManagement

from gitflowLibs.project_management.project_management_strategy import ProjectManagementStrategy

from properties import *


class Hotfix:

    # gitflow hotfix-start
    def hotfixStart(self, args):
        gitlab_helper = GitlabHelper()
        gitHelper = GitHelper()

        branch = HOTFIX_BRANCH.format(args.branch)
        gitHelper.createNewBranchFrom(MASTER_BRANCH, branch)

        title = args.title if args.title is not None else branch
        issue = args.issue if args.issue is not None else 0
        mergeRequest = gitlab_helper.createMergeRequest(gitHelper.getCurrentUrl(), branch, 'WIP: ' + title, None, issue,
                                                       MASTER_BRANCH, 'bug')
        print('Branch {} and mergeRequest {} as created'.format(branch, mergeRequest.iid))

    # gitflow hotfix-finish
    def hotfixFinish(self, args):
        gitlabHelper = GitlabHelper()
        gitHelper = GitHelper()

        branch = str(gitHelper.getCurrentBranch() if args.branch is None else args.branch)

        try:
            gitlabHelper.validateAndCloseMergeRequest(gitHelper.getCurrentUrl(), branch)
            gitHelper.getGit().checkout(MASTER_BRANCH)
            gitHelper.getGit().pull()

            print('Hotfix {} merged on {}'.format(branch, MASTER_BRANCH))

        except ValueError as e:
            print(str(e))
