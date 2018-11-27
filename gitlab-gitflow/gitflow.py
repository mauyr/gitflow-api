#!/usr/bin/env python

# setup
# curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
# sudo python get-pip.py
# sudo pip install gitpython
# sudo pip install --upgrade python-gitlab

import argparse

from routines.feature import Feature
from routines.hotfix import Hotfix
from routines.release import Release
from routines.changelog import Changelog


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('action', type=str,
                        help='Actions: feature-start, feature-finish, hotfix-start, hotfix-finish, release-start, '
                             'release-finish, launch, changelog')
    parser.add_argument('--branch', help='Branch name')
    parser.add_argument('--title', help='Title description of feature or hotfix')
    parser.add_argument('--issue', help='Issue ID on GitLab')
    parser.add_argument('--fromTag', help='Inital tag for changelog comparation')

    args = parser.parse_args()

    if args.action.lower() == 'feature-start':
        Feature().feature_start(args)
    elif args.action.lower() == 'feature-finish':
        Feature().feature_finish(args)
    elif args.action.lower() == 'hotfix-start':
        Hotfix().hotfixStart(args)
    elif args.action.lower() == 'hotfix-finish':
        Hotfix().hotfix_finish(args)
    elif args.action.lower() == 'release-start':
        Release().release_start()
    elif args.action.lower() == 'release-finish':
        Release().release_finish(args)
    elif args.action.lower() == 'launch':
        Release().launch()
    elif args.action.lower() == 'changelog':
        print(Changelog().create_changelog(args.branch))
    else:
        print(
            'Action not found [feature-start, feature-finish, hotfix-start, hotfix-finish, release-start, '
            'release-finish, launch, changelog]')


# main
main()
