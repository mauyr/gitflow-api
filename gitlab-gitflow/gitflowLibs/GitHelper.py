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

	def getCurrentUrl(self):
		return self.repo.remotes[0].url

	def getCurrentBranch(self):
		return self.repo.active_branch

	def createNewBranchFrom(self, fromBranch, newBranch):
		git_cmd = 'git checkout {}'
		check_call(git_cmd.format(fromBranch), shell=True)

		git_cmd = 'git checkout -b {}'
		check_call(git_cmd.format(newBranch), shell=True)

		git_cmd = 'git push -u origin {}'
		check_call(git_cmd.format(newBranch), shell=True)

	def commitAndPushUpdateMessage(self, branch, version):
		git_cmd = 'git add .'
		check_call(git_cmd, shell=True)

		git_cmd = 'git commit -m "Update to next version {}"'
		check_call(git_cmd.format(version), shell=True)

		git_cmd = 'git push -u origin {}'
		check_call(git_cmd.format(branch), shell=True)

	def createTag(self, tag, message):
		git_cmd = 'git tag -a {} -m "{}"'
		check_call(git_cmd.format(tag, message), shell=True)

		git_cmd = 'git push -u origin {}'
		check_call(git_cmd.format(tag), shell=True)

	def checkConflicts(self, branch):
		try:
			git_cmd = 'git merge --no-commit {}'
			check_call(git_cmd.format(branch), shell=True)
		except Exception:
			git_cmd = 'git reset HEAD --hard'
			check_call(git_cmd, shell=True)

			raise RuntimeError('Conflict with branch {}'.format(branch))

	def getGit(self):
		return self.repo.git