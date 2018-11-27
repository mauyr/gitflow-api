#!/usr/bin/env python

import os
from gitflowLibs.GitlabHelper import GitlabHelper
from gitflowLibs.GitHelper import GitHelper

from gitflowLibs.version_management import VersionManagement, Version

from gitflowLibs.project_management.project_management_strategy import ProjectManagementStrategy

from properties import *


class Release:

    # gitlab-gitflow release start
    def release_start(self):
        git = GitHelper()

        group_name, url_pattern = self._urlPatternBuild(git)

        initial_path = os.getcwd()

        git = GitHelper()
        git.getGit().checkout(STAGING_BRANCH)
        git.getGit().pull()

        git.checkConflicts(MASTER_BRANCH)

        # print(urlPattern)
        release_branch = RELEASE_BRANCH.format(self._recursive_release(initial_path, url_pattern, group_name))

        self._create_merge_requests(initial_path, release_branch)

        # Get back to initial directory
        os.chdir(initial_path)

    # gitlab-gitflow release finish
    def release_finish(self, args):
        gitlab_helper = GitlabHelper()
        git = GitHelper()
        path = os.getcwd()
        os.chdir(path)

        branch = str(git.getCurrentBranch() if args.branch is None else args.branch)

        if branch.lower().find('release') < 0:
            raise ValueError('Not valid release branch {}'.format(branch))

        # continue if dont have conflicts or merge request for release is merged
        try:
            gitlab_helper.validateAndCloseMergeRequest(git.getCurrentUrl(), branch)
        except RuntimeWarning as ex:
            print('Release branch merged!', ex)
        except ValueError as e:
            raise ValueError(e)

        # Sincronization merge request from master to staging to execute after finish release
        git.getGit().checkout(STAGING_BRANCH)
        git.getGit().pull()
        try:
            git.checkConflicts(MASTER_BRANCH)
        except Exception as e:
            print(e)
            gitlab_helper.createMergeRequest(git.getCurrentUrl(), MASTER_BRANCH,
                                             'Sincronization merge request {} to {}'.format(MASTER_BRANCH,
                                                                                            STAGING_BRANCH),
                                             'Don\'t remove this merge request before finish release', None,
                                             STAGING_BRANCH, None)
            gitlab_helper.validateMergeRequestByUrlAndBranches(git.getCurrentUrl(), MASTER_BRANCH,
                                                               STAGING_BRANCH)

        git.getGit().pull()

        new_version = VersionManagement.update_version(Version.MINOR, True)
        git.commitAndPushUpdateMessage(STAGING_BRANCH, new_version)

    def launch(self):
        git = GitHelper()
        git.getGit().checkout(MASTER_BRANCH)
        git.getGit().pull()

        path = os.getcwd()
        project_management = ProjectManagementStrategy().getInstance(path)

        version = project_management.actualVersion().replace('-SNAPSHOT', '')

        # TODO: Criar rotinas para release recursivos e verificar se todas as dependencias nao estao mais em snapshot
        project_management.updateVersion(version)
        project_management.updateDependenciesVersion()

        git.commitAndPushUpdateMessage('Prepare versions to release')

        group_name, project_name = self._extractGroupAndProjectFromUrl(git.getCurrentUrl())

        changelog = self._createChangelog(MASTER_BRANCH)

        git.createTag(VERSION.format(project_name, version), changelog)

        # update patch version for next tag
        new_version = VersionManagement.update_version(Version.PATCH, False)

        git.commitAndPushUpdateMessage(MASTER_BRANCH, new_version)

    # gitlab-gitflow release finish
    def create_changelog(self, args):
        git = GitHelper()
        branch = str(git.getCurrentBranch() if args.branch is None else args.branch)

        print(self._createChangelog(branch, fromTag=args.fromTag))

    def _recursive_release(self, actualPath, urlPattern, originGroupName):

        project_management = ProjectManagementStrategy().getInstance(actualPath)

        os.chdir(actualPath)

        project_management.updateDependenciesVersion()

        git = GitHelper()
        git.getGit().checkout(STAGING_BRANCH)
        git.getGit().pull()

        dependencies = project_management.dependencies()
        print('Total dependencies of {}: {}'.format(actualPath, len(dependencies)))

        if len(dependencies) > 0:
            for dependency in dependencies:
                path = self._checkoutDependency(STAGING_BRANCH, actualPath, dependency, originGroupName,
                                                urlPattern)
                try:
                    dependency_project_manager = ProjectManagementStrategy().getInstance(path)
                    os.chdir(path)
                    git = GitHelper()

                    dependency_version = dependency.version.replace('-SNAPSHOT', '')
                    git.getGit().checkout('release/' + dependency_version)

                    dependency_project_manager.deploy()
                except Exception as e:
                    self._recursive_release(path, urlPattern, originGroupName)

        try:
            os.chdir(actualPath)

            git = GitHelper()
            release_version = project_management.actualVersion().replace('-SNAPSHOT', '')

            print('Starting release of {}').format(os.getcwd())

            project_management.test()

            git.createNewBranchFrom(STAGING_BRANCH, RELEASE_BRANCH.format(release_version))

            project_management.deploy()

            return release_version
        except RuntimeError as e:
            print('Error creating release of {}: {}'.format(os.getcwd(), str(e)))

    # gitlab-gitflow release finish
    def _create_merge_requests(self, path, branch):
        os.chdir(path)

        git = GitHelper()
        group_name, url_pattern = self._urlPatternBuild(git)

        merge_requests = self._create_recursive_merge_request(branch, path, url_pattern, group_name)

        if merge_requests is not None:
            for mergeRequest in merge_requests:
                print('Merge request created: {}'.format(mergeRequest.iid))

    def _create_recursive_merge_request(self, branch, actual_path, url_pattern, origin_group_name):
        project_management = ProjectManagementStrategy().getInstance(actual_path)

        os.chdir(actual_path)
        git = GitHelper()
        merge_requests = []

        git.getGit().checkout(branch)
        git.getGit().pull()

        dependencies = project_management.dependencies()
        print('Total dependencies of {}: {}'.format(actual_path, len(dependencies)))

        if len(dependencies) > 0:
            for dependency in dependencies:
                release_version = dependency.version.replace('-SNAPSHOT', '')
                path = self._checkoutDependency('release/' + release_version, actual_path, dependency, origin_group_name,
                                                url_pattern)

                merge_requests.extend(
                    self._create_recursive_merge_request('release/' + release_version, path, url_pattern, origin_group_name))

        gitlab = GitlabHelper()

        mergeRequest = gitlab.findMergeRequestByUrlAndBranch(git.getCurrentUrl(), branch)
        if mergeRequest is None:
            description = str('## Merge requests\n')
            for createdMergeRequests in merge_requests:
                description = description + '* ' + createdMergeRequests.web_url.encode('utf-8').strip() + '\n'

            description = description + self._createChangelog(branch, path=actual_path)

            merge_requests.append(
                gitlab.createMergeRequest(git.getCurrentUrl(), branch, 'Release {} - ' + branch,
                                                description, None, self.MASTER_BRANCH, None))

        return merge_requests

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
            lastVersion = '{}.0.0'.format(self._extractVersion(actualVersion, Version.MAJOR) - 1)
            for tag in tags:
                tagCommit = tag
                tagVersion = str(tagCommit).replace(self.VERSION.format(projectName, ''), '')
                if self._diffVersion(tagVersion, lastVersion) <= 0:
                    break
        else:
            if self._extractVersion(tagVersion, Version.MINOR) != self._extractVersion(actualVersion, Version.MINOR):
                lastVersion = '{}.{}.0'.format(self._extractVersion(actualVersion, Version.MAJOR),
                                               self._extractVersion(actualVersion, Version.MINOR) - 1)
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
                    issue = Issue(mergeRequest.title, mergeRequest.web_url,
                                  mergeRequest.labels[0] if len(mergeRequest.labels) > 0 else 'others')
                    self._addChangeLogIssue(changelogIssues, issue)

            # ignore some commits
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
            groupName = str(url[len(url) - 2])
            projectName = str(url[len(url) - 1]).replace('.git', '')
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
