#!/usr/bin/env python
# encoding: utf-8
import argparse

from gitflow_api.services.feature import Feature
from gitflow_api.services.hotfix import Hotfix
from gitflow_api.services.release import Release
from gitflow_api.services.changelog import Changelog


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('action', type=str,
                        help='Actions: feature-start, feature-finish, hotfix-start, hotfix-finish, release-start, '
                             'release-finish, launch, changelog')
    parser.add_argument('--branch', help='Branch name')
    parser.add_argument('--title', help='Title description of feature or hotfix')
    parser.add_argument('--issue', help='Issue ID on GitLab')
    parser.add_argument('--fromTag', help='Initial tag for changelog comparing')
    parser.add_argument('--onlyStaging', nargs='?', const=True, help='Use only staging merge requests for changelog')
    parser.add_argument('--force', nargs='?', const=True, help='Force to recreate release')
    parser.add_argument('--skipTests', nargs='?', const=True, help='Skip tests')

    args = parser.parse_args()

    if args.action.lower() == 'feature-start':
        Feature().feature_start(args)
    elif args.action.lower() == 'feature-finish':
        Feature().feature_finish(args)
    elif args.action.lower() == 'hotfix-start':
        Hotfix().hotfix_start(args)
    elif args.action.lower() == 'hotfix-finish':
        Hotfix().hotfix_finish(args)
    elif args.action.lower() == 'release-start':
        Release().release_start(force=args.force, skipTests=args.skipTests)
    elif args.action.lower() == 'release-finish':
        Release().release_finish(args)
    elif args.action.lower() == 'launch':
        Release().launch()
    elif args.action.lower() == 'changelog':
        print(Changelog().create_markdown_changelog(args.branch, from_tag=args.fromTag, only_staging=args.onlyStaging))
    else:
        print(
            'Action not found [feature-start, feature-finish, hotfix-start, hotfix-finish, release-start, '
            'release-finish, launch, changelog]')


if __name__ == '__main__':
    main()