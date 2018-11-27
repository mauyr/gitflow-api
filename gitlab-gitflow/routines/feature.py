#!/usr/bin/env python

from properties import *

from gitlab.gitlab import Gitlab
from utilities.git_helper import GitHelper
from subprocess import check_call


class Feature:

    def feature_start(self, args):
        gitlab = Gitlab()
        git = GitHelper()

        mvn_cmd = 'mvn -DfeatureName={} -DallowSnapshots=true -DpushFeatures=true jgitflow:feature-start'.format(
            args.branch)
        check_call([mvn_cmd], shell=True)

        branch = FEATURE_BRANCH.format(args.branch)
        title = args.title if args.title is not None else branch
        issue = args.issue if args.issue is not None else 0
        merge_request = gitlab.create_merge_request(git.get_current_url(), branch, 'WIP: ' + title, '', issue,
                                                    STAGING_BRANCH, 'story')
        print('Branch {} and merge_request {} as created'.format(branch, merge_request.iid))


    def feature_finish(self, args):
        gitlab = Gitlab()
        git = GitHelper()

        branch = str(git.get_current_branch() if args.branch is None else args.branch)

        try:
            gitlab.validate_and_close_merge_request(git.get_current_url(), branch)
            git.get_git_cmd().checkout(STAGING_BRANCH)
            git.get_git_cmd().pull()

            print('Feature {} merged on {}'.format(branch, FEATURE_BRANCH))

        except ValueError as e:
            print(str(e))
