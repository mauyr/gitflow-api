#!/usr/bin/env python

from properties import *

from gitflowLibs.GitlabHelper import GitlabHelper
from gitflowLibs.GitHelper import GitHelper
from subprocess import call, check_call


class Feature:

    # gitlab-gitflow feature start
    def feature_start(self, args):
        gitlab = GitlabHelper()
        git = GitHelper()

        mvn_cmd = 'mvn -DfeatureName={} -DallowSnapshots=true -DpushFeatures=true jgitflow:feature-start'.format(
            args.branch)
        check_call([mvn_cmd], shell=True)

        branch = FEATURE_BRANCH.format(args.branch)
        title = args.title if args.title is not None else branch
        issue = args.issue if args.issue is not None else 0
        merge_request = gitlab.createMergeRequest(git.getCurrentUrl(), branch, 'WIP: ' + title, '', issue,
                                                  STAGING_BRANCH, 'story')
        print('Branch {} and merge_request {} as created'.format(branch, merge_request.iid))


    # gitlab-gitflow feature finish
    def feature_finish(self, args):
        gitlabHelper = GitlabHelper()
        gitHelper = GitHelper()

        branch = str(gitHelper.getCurrentBranch() if args.branch is None else args.branch)

        try:
            gitlabHelper.validateAndCloseMergeRequest(gitHelper.getCurrentUrl(), branch)
            gitHelper.getGit().checkout(STAGING_BRANCH)
            gitHelper.getGit().pull()

            print('Feature {} merged on {}'.format(branch, FEATURE_BRANCH))

        except ValueError as e:
            print(str(e))
