#!/usr/bin/env python

import requests, os, gitlab


class GitlabHelper:
	global gl
	global api_url
	global api_key
	global path

	def __init__(self):
		self.api_key = os.environ['GITLAB_KEY']
		self.api_url = os.environ['GITLAB_URL']

		self.path = os.getcwd()

		self.data = []
		self.gl = gitlab.Gitlab(self.api_url, private_token=self.api_key)

	def findMergeRequestByUrlAndBranch(self, gitUrl, branch):
		project = self.findProjectByUrl(gitUrl)

		return self.findMergeRequestByProjectAndBranch(project, branch)

	def findMergeRequestByProjectAndBranch(self, project, branch):
		if project.mergerequests is None:
			return None

		mergeRequests = project.mergerequests.list(state='opened')

		filteredMergeRequests = list(filter(lambda x: str(x.source_branch) == str(branch), mergeRequests))
		if len(filteredMergeRequests) == 0:
			return None
		else:
			return filteredMergeRequests[0]

	def _findMergeRequestByUrlAndBranches(self, gitUrl, branchFrom, branchTo):
		project = self.findProjectByUrl(gitUrl)

		if project.mergerequests is None:
			return None

		mergeRequests = project.mergerequests.list(state='opened')


		filteredMergeRequests = list(
			filter(lambda x: str(x.source_branch) == str(branchFrom) and str(x.target_branch) == str(branchTo),
				   mergeRequests))
		if len(filteredMergeRequests) == 0:
			return None
		else:
			return filteredMergeRequests[0]

	def findMergeRequestByCommitMessage(self, commitMessage):
		mergeRequestCode = commitMessage[commitMessage.find('See merge request ') + 18:]

		groupName = mergeRequestCode[:mergeRequestCode.find('/')]
		projectName = mergeRequestCode[mergeRequestCode.find('/') + 1:mergeRequestCode.find('!')]
		mergeRequestId = mergeRequestCode[mergeRequestCode.find('!') + 1:].replace('\n', '')

		group = self.findGroupByName(groupName)
		project = self._findProjectByGroupAndName(group, projectName)
		return project.mergerequests.get(mergeRequestId)

	def findProjectByUrl(self, url):
		groupName, projectName = self._extractGroupAndProjectFromUrl(url)
		group = self.findGroupByName(groupName)

		return self._findProjectByGroupAndName(group, projectName)

	def findGroupByName(self, groupName):
		return self.gl.groups.get(groupName)

	def _findProjectByGroupAndName(self, group, projectName):
		projects = group.projects.list(all=True)
		project = list(filter(lambda x: x.name == projectName, projects))[0]
		return self.gl.projects.get(project.id)

	def _makeMergeRequestDescription(self, model, description, issueId):
		if description is not None:
			return description

		if model is not None:
			replacedModel = model
		else:
			replacedModel = 'Closes #0'

		if issueId is not None:
			replacedModel.replace('Closes #0', 'Closes #' + str(issueId))

		return replacedModel

	def _getMergeRequestMD(self, path):
		mergeRequestMDFile = path + '/.gitlab/merge_request_templates/merge_request.md'

		if os.path.exists(mergeRequestMDFile):
			F = open(mergeRequestMDFile, 'r')
			return F.read()
		else:
			return None

	def createMergeRequest(self, gitUrl, branchFrom, title, description, issueId, toBranch, label):
		project = self.findProjectByUrl(gitUrl)

		mergeRequest = self._findMergeRequestByUrlAndBranches(gitUrl, branchFrom, toBranch)

		if mergeRequest is None:
			mergeRequestMD = self._getMergeRequestMD(self.path)

			description = self._makeMergeRequestDescription(mergeRequestMD, description, issueId)
			labels = []
			if (label is not None):
				labels = [label]

			mergeRequestModel = {
				'source_branch': branchFrom,
				'target_branch': toBranch,
				'title': (branchFrom if title is None else title),
				'labels': labels,
				'description': description,
				'remove_source_branch': True
			}

			mergeRequest = project.mergerequests.create(mergeRequestModel)

		return mergeRequest

	def _validateMergeRequest(self, mergeRequest):
		if mergeRequest is None:
			raise RuntimeWarning('Merge request not found for current branch')

		if bool(mergeRequest.work_in_progress):
			raise ValueError('Merge Request {} - {} on WIP status'.format(mergeRequest.iid, mergeRequest.title))

		if bool(mergeRequest.discussion_locked):
			raise ValueError(
				'Merge Request {} - {} has discussion unresolved'.format(mergeRequest.iid, mergeRequest.title))

		if str(mergeRequest.merge_status) != 'can_be_merged':
			raise ValueError(
				'Merge Request {} - {} is not ready for merge'.format(mergeRequest.iid, mergeRequest.title))

		return True

	def validateMergeRequestByUrlAndBranch(self, gitUrl, branch):
		mergeRequest = self.findMergeRequestByUrlAndBranch(gitUrl, branch)
		return self._validateMergeRequest(mergeRequest)

	def validateMergeRequestByUrlAndBranches(self, gitUrl, branchFrom, branchTo):
		mergeRequest = self._findMergeRequestByUrlAndBranches(gitUrl, branchFrom, branchTo)

		return self._validateMergeRequest(mergeRequest)

	def validateAndCloseMergeRequest(self, gitUrl, branch):
		mergeRequest = self.findMergeRequestByUrlAndBranch(gitUrl, branch)

		if self._validateMergeRequest(mergeRequest):
			mergeRequest.merge()

	def validateAndCloseMergeRequestByBranches(self, gitUrl, branchFrom, branchTo):
		mergeRequest = self._findMergeRequestByUrlAndBranches(gitUrl, branchFrom, branchTo)

		if self._validateMergeRequest(mergeRequest):
			mergeRequest.merge()

	def _extractGroupAndProjectFromUrl(self, originUrl):
		if (str(originUrl).find('http') >= 0):
			url = originUrl.split('/')
			groupName = str(url[len(url) - 2])
			projectName = str(url[len(url) - 1]).replace('.git', '')
			return groupName, projectName
		else:
			url = originUrl.split('/')
			groupName = str(url[0][url[0].rfind(':') + 1:])
			projectName = str(url[1]).replace('.git', '')
			return groupName, projectName
