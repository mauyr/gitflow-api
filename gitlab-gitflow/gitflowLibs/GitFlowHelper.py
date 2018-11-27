#!/usr/bin/env python

import os
from gitflowLibs.GitlabHelper import GitlabHelper
from gitflowLibs.GitHelper import GitHelper
from subprocess import call, check_call

from gitflowLibs.version_management import VersionManagement

from gitflowLibs.project_management.project_management_strategy import ProjectManagementStrategy

from properties import *


class GitFlowHelper:

	# gitlab-gitflow feature start
	def featureStart(self, args):
		gitlabHelper = GitlabHelper()
		gitHelper = GitHelper()

		mvn_cmd = 'mvn -DfeatureName={} -DallowSnapshots=true -DpushFeatures=true jgitflow:feature-start'.format(
			args.branch)
		call([mvn_cmd], shell=True)

		branch = FEATURE_BRANCH.format(args.branch)
		title = args.title if args.title is not None else branch
		issue = args.issue if args.issue is not None else 0
		mergeRequest = gitlabHelper.createMergeRequest(gitHelper.getCurrentUrl(), branch, 'WIP: ' + title, '', issue,
													   self.STAGING_BRANCH, 'story')
		print('Branch {} and mergeRequest {} as created'.format(branch, mergeRequest.iid))


	# gitlab-gitflow feature finish
	def featureFinish(self, args):
		gitlabHelper = GitlabHelper()
		gitHelper = GitHelper()

		branch = str(gitHelper.getCurrentBranch() if args.branch is None else args.branch)

		try:
			gitlabHelper.validateAndCloseMergeRequest(gitHelper.getCurrentUrl(), branch)
			gitHelper.getGit().checkout(self.STAGING_BRANCH)
			gitHelper.getGit().pull()

			print('Feature {} merged on {}'.format(branch, self.FEATURE_BRANCH))

		except ValueError as e:
			print(str(e))


	# gitlab-gitflow hotfix start
	def hotfixStart(self, args):
		gitlabHelper = GitlabHelper()
		gitHelper = GitHelper()

		branch = self.HOTFIX_BRANCH.format(args.branch)
		gitHelper.createNewBranchFrom(self.MASTER_BRANCH, branch)

		title = args.title if args.title is not None else branch
		issue = args.issue if args.issue is not None else 0
		mergeRequest = gitlabHelper.createMergeRequest(gitHelper.getCurrentUrl(), branch, 'WIP: '+ title, None, issue,
													   self.MASTER_BRANCH, 'bug')
		print('Branch {} and mergeRequest {} as created'.format(branch, mergeRequest.iid))


	# gitlab-gitflow hotfix finish
	def hotfixFinish(self, args):
		gitlabHelper = GitlabHelper()
		gitHelper = GitHelper()

		branch = str(gitHelper.getCurrentBranch() if args.branch is None else args.branch)

		try:
			gitlabHelper.validateAndCloseMergeRequest(gitHelper.getCurrentUrl(), branch)
			gitHelper.getGit().checkout(self.MASTER_BRANCH)
			gitHelper.getGit().pull()

			print('Hotfix {} merged on {}'.format(branch, self.MASTER_BRANCH))

		except ValueError as e:
			print(str(e))


	# gitlab-gitflow release start
	def releaseStart(self, args):
		gitHelper = GitHelper()

		groupName, urlPattern = self._urlPatternBuild(gitHelper)

		initialPath = os.getcwd()

		gitHelper = GitHelper()
		gitHelper.getGit().checkout(self.STAGING_BRANCH)
		gitHelper.getGit().pull()

		gitHelper.checkConflicts(self.MASTER_BRANCH)

		# print(urlPattern)
		releasebranch = self.RELEASE_BRANCH.format(self._recursiveRelease(initialPath, urlPattern, groupName))

		self._createMergeRequests(initialPath, releasebranch)

		# Get back to initial directory
		os.chdir(initialPath)

	# gitlab-gitflow release finish
	def releaseFinish(self, args):
		gitlabHelper = GitlabHelper()
		gitHelper = GitHelper()
		path = os.getcwd()
		os.chdir(path)

		branch = str(gitHelper.getCurrentBranch() if args.branch is None else args.branch)

		if (branch.lower().find('release') < 0):
			raise ValueError('Not valid release branch {}'.format(branch))

		#continue if dont have conflicts or merge request for release is merged
		try:
			gitlabHelper.validateAndCloseMergeRequest(gitHelper.getCurrentUrl(), branch)
		except RuntimeWarning as ex:
			print('Release branch merged!')
		except ValueError as e:
			raise ValueError(e)

		#Sincronization merge request from master to staging to execute after finish release
		gitHelper.getGit().checkout(self.STAGING_BRANCH)
		gitHelper.getGit().pull()
		try:
			gitHelper.checkConflicts(self.MASTER_BRANCH)
		except Exception as e:
			print(e)
			gitlabHelper.createMergeRequest(gitHelper.getCurrentUrl(), self.MASTER_BRANCH, 'Sincronization merge request {} to {}'.format(self.MASTER_BRANCH, self.STAGING_BRANCH), 'Don\'t remove this merge request before finish release', None, self.STAGING_BRANCH, None)
			gitlabHelper.validateMergeRequestByUrlAndBranches(gitHelper.getCurrentUrl(), self.MASTER_BRANCH, self.STAGING_BRANCH)

		gitHelper.getGit().pull()

		newVersion = self._updateVersion(Version.MINOR, True)
		gitHelper.commitAndPushUpdateMessage(self.STAGING_BRANCH, newVersion)

	##update version for next release
	def _updateVersion(self, versionUpdate, isSnapshot):
		return VersionManagement.update_version(versionUpdate, isSnapshot)

	def _getNewVersion(self, version, versionType, isSnapshot, increment):
		return VersionManagement.get_new_version(version, versionType, isSnapshot, increment)

	def launch(self, args):
		gitHelper = GitHelper()
		gitHelper.getGit().checkout(self.MASTER_BRANCH)
		gitHelper.getGit().pull()

		path = os.getcwd()
		projectManagement = ProjectManagementStrategy().getInstance(path)

		version = projectManagement.actualVersion().replace('-SNAPSHOT', '')

		#TODO: Criar rotinas para release recursivos e verificar se todas as dependencias nao estao mais em snapshot
		projectManagement.updateVersion(version)
		projectManagement.updateDependenciesVersion()

		gitHelper.commitAndPushUpdateMessage('Prepare versions to release')

		groupName, projectName = self._extractGroupAndProjectFromUrl(gitHelper.getCurrentUrl())

		changelog = self._createChangelog(self.MASTER_BRANCH)

		gitHelper.createTag(self.VERSION.format(projectName, version), changelog)

		#update patch version for next tag
		newVersion = self._updateVersion(Version.PATCH, False)

		gitHelper.commitAndPushUpdateMessage(self.MASTER_BRANCH, newVersion)


	# gitlab-gitflow release finish
	def createChangeLog(self, args):
		gitHelper = GitHelper()
		branch = str(gitHelper.getCurrentBranch() if args.branch is None else args.branch)

		print(self._createChangelog(branch, fromTag=args.fromTag))

	def _recursiveRelease(self, actualPath, urlPattern, originGroupName):

		projectManagement = ProjectManagementStrategy().getInstance(actualPath)

		os.chdir(actualPath)

		projectManagement.updateDependenciesVersion()

		gitHelper = GitHelper()
		gitHelper.getGit().checkout(self.STAGING_BRANCH)
		gitHelper.getGit().pull()

		dependencies = projectManagement.dependencies()
		print('Total dependencies of {}: {}'.format(actualPath, len(dependencies)))

		if len(dependencies) > 0:
			for dependency in dependencies:
				path = self._checkoutDependency(self.STAGING_BRANCH, actualPath, dependency, originGroupName, urlPattern)
				try:
					dependencyProjectManagement = ProjectManagementStrategy().getInstance(path)
					os.chdir(path)
					gitHelper = GitHelper()

					dependencyVersion = dependency.version.replace('-SNAPSHOT', '')
					gitHelper.getGit().checkout('release/' + dependencyVersion)

					dependencyProjectManagement.deploy()
				except Exception as e:
					self._recursiveRelease(path, urlPattern, originGroupName)

		try:
			os.chdir(actualPath)

			gitHelper = GitHelper()
			releaseVersion = projectManagement.actualVersion().replace('-SNAPSHOT', '')

			print('Starting release of {}').format(os.getcwd())

			projectManagement.test()

			gitHelper.createNewBranchFrom(self.STAGING_BRANCH, self.RELEASE_BRANCH.format(releaseVersion))

			projectManagement.deploy()

			return releaseVersion
		except RuntimeError as e:
			print('Error creating release of {}: {}'.format(os.getcwd(), str(e)))

	# gitlab-gitflow release finish
	def _createMergeRequests(self, path, branch):
		os.chdir(path)

		gitHelper = GitHelper()
		groupName, urlPattern = self._urlPatternBuild(gitHelper)

		mergeRequests = self._createRecursiveMergeRequest(branch, path, urlPattern, groupName)

		if mergeRequests is not None:
			for mergeRequest in mergeRequests:
				print('Merge request created: {}'.format(mergeRequest.iid))


	def _createRecursiveMergeRequest(self, branch, actualPath, urlPattern, originGroupName):
		projectManagement = ProjectManagementStrategy().getInstance(actualPath)

		os.chdir(actualPath)
		gitHelper = GitHelper()
		mergeRequests = []

		gitHelper.getGit().checkout(branch)
		gitHelper.getGit().pull()

		dependencies = projectManagement.dependencies()
		print('Total dependencies of {}: {}'.format(actualPath, len(dependencies)))

		if len(dependencies) > 0:
			for dependency in dependencies:
				releaseVersion = dependency.version.replace('-SNAPSHOT', '')
				path = self._checkoutDependency('release/' + releaseVersion, actualPath, dependency, originGroupName, urlPattern)

				mergeRequests.extend(self._createRecursiveMergeRequest('release/' + releaseVersion, path, urlPattern, originGroupName))

		gitlabhelper = GitlabHelper()

		mergeRequest = gitlabhelper.findMergeRequestByUrlAndBranch(gitHelper.getCurrentUrl(), branch)
		if mergeRequest is None:
			description = str('## Merge requests\n')
			for createdMergeRequests in mergeRequests:
				description = description + '* ' + createdMergeRequests.web_url.encode('utf-8').strip() + '\n'

			description = description + self._createChangelog(branch, path=actualPath)

			mergeRequests.append(gitlabhelper.createMergeRequest(gitHelper.getCurrentUrl(), branch, 'Release {} - ' + branch, description, None, self.MASTER_BRANCH, None))

		return mergeRequests

	def _checkoutDependency(self, branch, actualPath, dependency, originGroupName, urlPattern):
		print('Checkout from {} dependency {}'.format(actualPath, dependency.artifactId))

		group = originGroupName
		sharedProjects = list(filter(lambda x: dependency.artifactId == x.project, self._getSharedProjects()))
		if len(sharedProjects) > 0:
			group = sharedProjects[0].group
		sharedProjects = list(filter(lambda x: dependency.artifactId == x.project, self._getSharedProjects()))
		if len(sharedProjects) > 0:
			group = sharedProjects[0].group

		path = '../{}'.format(dependency.artifactId)
		if not os.path.exists(path):
			print('Cloning repository: {}'.format(urlPattern.format(group, dependency.artifactId)))
			newRepo = GitHelper()
			newRepo.repo.clone_from(urlPattern.format(group, dependency.artifactId), path)

			os.chdir(path)
			gitHelper = GitHelper()
			gitHelper.getGit().checkout(branch)
			gitHelper.getGit().pull()

		return path

	def _createChangelog(self, branch, fromTag=None, path=None):

		if path is not None:
			os.chdir(path)

		gitHelper = GitHelper()
		gitHelper.getGit().checkout(branch)
		gitHelper.getGit().pull()

		if len(gitHelper.repo.tags) == 0:
			return ''

		tagCommit = ''
		if fromTag is not None:
			tagCommit = gitHelper.repo.tags[fromTag].commit
		else:
			tags = sorted(gitHelper.repo.tags, key=lambda x: x.commit.authored_date, reverse=True)

			groupName, projectName = self._extractGroupAndProjectFromUrl(gitHelper.getCurrentUrl())
			tagCommit = self._findLastTag(projectName, tags)

		print('Creating changelog from {}'.format(str(tagCommit)))
		log = gitHelper.getGit().log(str(tagCommit) + '..HEAD').split('\n')

		commits = self._getCommitByLog(log)

		changelogIssues = self._normalizeIssues(commits)

		return self._makeChangeLogMD(changelogIssues)

	def _findLastTag(self, projectName, tags):
		path = os.getcwd()

		projectManagement = ProjectManagementStrategy().getInstance(path)
		actualVersion = projectManagement.actualVersion().replace('-SNAPSHOT', '')
		# ultima tag
		tagCommit = tags[0]
		tagVersion = str(tagCommit).replace(self.VERSION.format(projectName, ''), '')

		if self._extractVersion(tagVersion, Version.MAJOR) != self._extractVersion(actualVersion, Version.MAJOR):
			lastVersion = '{}.0.0'.format(self._extractVersion(actualVersion, Version.MAJOR)-1)
			for tag in tags:
				tagCommit = tag
				tagVersion = str(tagCommit).replace(self.VERSION.format(projectName, ''), '')
				if self._diffVersion(tagVersion, lastVersion) <= 0:
					break
		else:
			if self._extractVersion(tagVersion, Version.MINOR) != self._extractVersion(actualVersion, Version.MINOR):
				lastVersion = '{}.{}.0'.format(self._extractVersion(actualVersion, Version.MAJOR), self._extractVersion(actualVersion, Version.MINOR)-1)
				for tag in tags:
					tagCommit = tag
					tagVersion = str(tagCommit).replace(self.VERSION.format(projectName, ''), '')
					if self._diffVersion(tagVersion, lastVersion) <= 0:
						break

		return tagCommit

	def _diffVersion(self, version1, version2):
		return VersionManagement.diff_version(version1, version2)

	def _extractVersion(self, version, versionType):
		return VersionManagement._extractVersion(version, versionType)


	def _normalizeIssues(self, commits):
		gitlabHelper = GitlabHelper()
		changelogIssues = ChangelogIssues()

		for commit in commits:
			# print(commit.commit)
			# print(commit.message)

			message = commit.message
			if message.find('See merge request') >= 0:
				mergeRequest = gitlabHelper.findMergeRequestByCommitMessage(message)
				if mergeRequest.title.find('release/') == -1:
					issue = Issue(mergeRequest.title, mergeRequest.web_url, mergeRequest.labels[0] if len(mergeRequest.labels)>0 else 'others')
					self._addChangeLogIssue(changelogIssues, issue)

			#ignore some commits
			elif message.find('[maven-release-plugin]') >= 0 or message.find('Merge branch') >= 0:
				pass

		return changelogIssues

	def _addChangeLogIssue(self, changelogIssues, issue):
		if issue.issueType == 'ignore':
			pass
		elif issue.issueType == 'story':
			changelogIssues.stories.append(issue)
		elif issue.issueType == 'bug':
			changelogIssues.bugs.append(issue)
		elif issue.issueType == 'technical debt':
			changelogIssues.technicalDebts.append(issue)
		else:
			changelogIssues.others.append(issue)

	def _makeChangeLogMD(self, changelogIssues):
		mergeRequestMD = ''
		if len(changelogIssues.stories) > 0:
			mergeRequestMD = mergeRequestMD + '\n' + str('## Melhorias')
			for issue in changelogIssues.stories:
				mergeRequestMD = mergeRequestMD + '\n' + str('* [{}]({})').format(issue.title, issue.url)

		if len(changelogIssues.bugs) > 0:
			mergeRequestMD = mergeRequestMD + '\n' + str('## Correcoes')
			for issue in changelogIssues.bugs:
				mergeRequestMD = mergeRequestMD + '\n' + str('* [{}]({})').format(issue.title, issue.url)

		if len(changelogIssues.technicalDebts) > 0:
			mergeRequestMD = mergeRequestMD + '\n' + str('## Debitos Tecnicos')
			for issue in changelogIssues.technicalDebts:
				mergeRequestMD = mergeRequestMD + '\n' + str('* [{}]({})').format(issue.title, issue.url)

		if len(changelogIssues.others) > 0:
			mergeRequestMD = mergeRequestMD + '\n' + str('## Outros')
			for issue in changelogIssues.others:
				mergeRequestMD = mergeRequestMD + '\n' + str('* [{}]({})').format(issue.title, issue.url)

		return mergeRequestMD


	def _getCommitByLog(self, log):
		commits = []
		actualCommit = Commit()
		for logLine in log:
			line = logLine.encode('utf-8').strip()
			if line.find('commit') >= 0:
				if actualCommit.commit != '':
					commits.append(actualCommit)
				actualCommit = Commit()
				actualCommit.commit = line.replace('commit ', '')
			elif line.find('Author:') >= 0:
				actualCommit.author = line.replace('Author: ', '')
			elif line.find('Date:') >= 0:
				actualCommit.date = line.replace('Date:   ', '')
			else:
				actualCommit.message = actualCommit.message + ('' if actualCommit.message == '' else '\n') + str(line)

		return commits

	# List of shared projects
	def _getSharedProjects(self):
		projects = []
		projects.append(Project('rf-dominio', 'desenvolvimento'))
		projects.append(Project('rf-adapters', 'desenvolvimento'))
		projects.append(Project('rf-canonico-aereo', 'gateway'))
		projects.append(Project('rf-client-sabre', 'gateway'))
		return projects

	def _urlPatternBuild(self, gitHelper):
		url = gitHelper.getCurrentUrl().split('/')
		groupName = str(url[0][url[0].rfind(':') + 1:])
		url[0] = str(url[len(url) - 2]).replace(groupName, '{}')
		url[1] = '{}'
		urlPattern = '/'.join(url)
		return groupName, urlPattern

	def _extractGroupAndProjectFromUrl(self, originUrl):
		if (str(originUrl).find('http') >= 0):
			url = originUrl.split('/')
			groupName = str(url[len(url)-2])
			projectName = str(url[len(url)-1]).replace('.git', '')
			return groupName, projectName
		else:
			url = originUrl.split('/')
			groupName = str(url[0][url[0].rfind(':') + 1:])
			projectName = str(url[1]).replace('.git', '')
			return groupName, projectName

class ChangelogIssues:
	stories = []
	bugs = []
	technicalDebts = []
	others = []

class Issue:
	title = ''
	url = ''
	issueType = ''

	def __init__(self, title, url, issueType):
		self.title = title.encode('utf-8').strip()
		self.url = url.encode('utf-8').strip()
		self.issueType = issueType.encode('utf-8').strip()

class Commit:
	commit = ''
	author = ''
	date = ''
	message = ''

class Project:
	project = ''
	group = ''

	def __init__(self, project, group):
		self.project = str(project)
		self.group = str(group)