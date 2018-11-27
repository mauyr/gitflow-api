#!/usr/bin/env python

# setup
# curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
# sudo python get-pip.py
# sudo pip install gitpython
# sudo pip install --upgrade python-gitlab

import argparse
from gitflowLibs.GitFlowHelper import GitFlowHelper


def main():
	parser = argparse.ArgumentParser()

	parser.add_argument('action', type=str,
						help='Actions: feature-start, feature-finish, hotfix-start, hotfix-finish, release-start, release-finish, launch')
	parser.add_argument('--branch', help='Branch name')
	parser.add_argument('--title', help='Title description of feature or hotfix')
	parser.add_argument('--issue', help='Issue ID on GitLab')
	parser.add_argument('--fromTag', help='Inital tag for changelog comparation')

	args = parser.parse_args()

	if args.action.lower() == 'feature-start':
		GitFlowHelper().featureStart(args)
	elif args.action.lower() == 'feature-finish':
		GitFlowHelper().featureFinish(args)
	elif args.action.lower() == 'hotfix-start':
		GitFlowHelper().hotfixStart(args)
	elif args.action.lower() == 'hotfix-finish':
		GitFlowHelper().hotfixFinish(args)
	elif args.action.lower() == 'release-start':
		GitFlowHelper().releaseStart(args)
	elif args.action.lower() == 'release-finish':
		GitFlowHelper().releaseFinish(args)
	elif args.action.lower() == 'launch':
		GitFlowHelper().launch(args)
	elif args.action.lower() == 'changelog':
		GitFlowHelper().createChangeLog(args)
	else:
		print('Action not found [feature-start, feature-finish, hotfix-start, hotfix-finish, release-start, release-finish, launch]')

# main
main()
