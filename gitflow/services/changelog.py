#!/usr/bin/env python
# encoding: utf-8

import os

from gitflow.api.api_strategy import ApiStrategy
from gitflow.config.properties import *
from gitflow.utilities.git_helper import GitHelper
from gitflow.project.project_manager_strategy import ProjectManagerStrategy
from gitflow.utilities.version_utils import VersionUtils, Version

STORY_TYPE = 'story'
BUG_TYPE = 'bug'
TECHNICAL_TYPE = 'technical_debt'
OTHER_TYPE = 'other'
IGNORE_TYPE = 'ignore'


class Changelog:

    def __init__(self):
        pass

    def create_changelog(self, branch, from_tag=None, path=None):
        git = GitHelper()
        branch = str(git.get_current_branch() if branch is None else branch)

        return self._create_changelog(branch, from_tag=from_tag, path=path)

    def _create_changelog(self, branch, from_tag=None, path=None):

        if path is not None:
            os.chdir(path)

        git = GitHelper()
        git.checkout_and_pull(branch)

        if len(git.repo.tags) == 0:
            return ''

        tag_commit = ''
        if from_tag is not None:
            tag_commit = git.repo.tags[from_tag].commit
        else:
            tags = sorted(git.repo.tags, key=lambda x: x.commit.authored_date, reverse=True)

            group_name, project_name = git.extract_group_and_project()
            tag_commit = self._find_last_tag(project_name, tags)

        print('Creating changelog from {}'.format(str(tag_commit)))
        log = git.get_git_cmd().log(str(tag_commit) + '..HEAD').split('\n')

        commits = self._get_commit_by_log(log)

        changelog_issues = self._normalize_issues(commits)

        return self._make_changelog_md(changelog_issues)

    def _find_last_tag(self, project_name, tags):
        path = os.getcwd()

        project_management = ProjectManagerStrategy.get_instance(path)
        actual_version = project_management.actual_version().replace('-SNAPSHOT', '')
        # ultima tag
        tag_commit = tags[0]
        tag_version = str(tag_commit).replace(VERSION.format(project_name, ''), '')

        if VersionUtils.extract_version(tag_version, Version.MAJOR) != VersionUtils.extract_version(
                actual_version, Version.MAJOR):
            last_version = '{}.0.0'.format(VersionUtils.extract_version(actual_version, Version.MAJOR) - 1)
            for tag in tags:
                tag_commit = tag
                tag_version = str(tag_commit).replace(VERSION.format(project_name, ''), '')

                if VersionUtils.diff_version(tag_version, last_version) <= 0:
                    break
        else:

            if VersionUtils.extract_version(tag_version, Version.MINOR) != VersionUtils.extract_version(
                    actual_version, Version.MINOR):
                last_version = '{}.{}.0'.format(VersionUtils.extract_version(actual_version, Version.MAJOR),
                                                VersionUtils.extract_version(actual_version, Version.MINOR) - 1)
                for tag in tags:
                    tag_commit = tag
                    tag_version = str(tag_commit).replace(VERSION.format(project_name, ''), '')

                    if VersionUtils.diff_version(tag_version, last_version) <= 0:
                        break

        return tag_commit

    def _normalize_issues(self, commits):
        api = ApiStrategy.get_instance(os.getcwd())
        changelog_issues = ChangelogIssues()

        for commit in commits:
            # print(commit.commit)
            # print(commit.message)

            message = commit.message
            if message.find('See merge request') >= 0:
                merge_request = api.get_merge_request_api().find_merge_request_by_commit_message(message)
                if merge_request.source_branch.find(RELEASE_BRANCH.format('')) == -1:
                    issue = Issue(merge_request.title, merge_request.web_url,
                                  merge_request.labels)
                    self._add_change_log_issue(changelog_issues, issue)

            # ignore some commits
            elif message.find('[maven-release-plugin]') >= 0 or message.find('Merge branch') >= 0:
                pass

        return changelog_issues

    def _add_change_log_issue(self, changelog_issues, issue):
        if issue.issueType == IGNORE_TYPE:
            pass
        elif issue.issueType == STORY_TYPE:
            changelog_issues.stories.append(issue)
        elif issue.issueType == BUG_TYPE:
            changelog_issues.bugs.append(issue)
        elif issue.issueType == TECHNICAL_TYPE:
            changelog_issues.technicalDebts.append(issue)
        else:
            changelog_issues.others.append(issue)

    def _get_commit_by_log(self, log):
        commits = []
        actual_commit = Commit()
        for logLine in log:
            line = str(logLine.encode('utf-8').strip())
            if line.find('commit') >= 0:
                if actual_commit.commit != '':
                    commits.append(actual_commit)
                actual_commit = Commit()
                actual_commit.commit = line.replace('commit ', '')
            elif line.find('Author:') >= 0:
                actual_commit.author = line.replace('Author: ', '')
            elif line.find('Date:') >= 0:
                actual_commit.date = line.replace('Date:   ', '')
            else:
                actual_commit.message = actual_commit.message + ('' if actual_commit.message == '' else '\n') + str(
                    line)

        return commits

    def _make_changelog_md(self, changelog_issues):
        merge_request_md = ''
        if len(changelog_issues.stories) > 0:
            merge_request_md = merge_request_md + '\n' + str('## Improvements')
            for issue in changelog_issues.stories:
                merge_request_md = merge_request_md + '\n' + str('* [{}]({})').format(issue.title, issue.url)

        if len(changelog_issues.bugs) > 0:
            merge_request_md = merge_request_md + '\n' + str('## Bugs')
            for issue in changelog_issues.bugs:
                merge_request_md = merge_request_md + '\n' + str('* [{}]({})').format(issue.title, issue.url)

        if len(changelog_issues.technicalDebts) > 0:
            merge_request_md = merge_request_md + '\n' + str('## Technical Debts')
            for issue in changelog_issues.technicalDebts:
                merge_request_md = merge_request_md + '\n' + str('* [{}]({})').format(issue.title, issue.url)

        if len(changelog_issues.others) > 0:
            merge_request_md = merge_request_md + '\n' + str('## Others')
            for issue in changelog_issues.others:
                merge_request_md = merge_request_md + '\n' + str('* [{}]({})').format(issue.title, issue.url)

        return merge_request_md


class ChangelogIssues:
    stories = []
    bugs = []
    technicalDebts = []
    others = []

    def __init__(self):
        pass


class Issue:
    title = ''
    url = ''
    issueType = ''

    def __init__(self, title, url, labels):
        self.title = str(title)
        self.url = str(url)
        self.issueType = self._getIssueType(labels)

    def _getIssueType(self, labels):
        if len(list(filter(lambda x: str(x).find(VERSION_LABEL_PREFIX.format('')) == 0, labels))) > 0 or len(set(IGNORE_LABELS) & set(labels)) > 0:
            return IGNORE_TYPE
        elif len(set(FEATURE_LABELS) & set(labels)) > 0:
            return STORY_TYPE
        elif len(set(BUG_LABELS) & set(labels)) > 0:
            return BUG_TYPE
        elif len(set(TECHNICAL_DEBT_LABELS) & set(labels)) > 0:
            return TECHNICAL_TYPE
        else:
            return OTHER_TYPE


class Commit:
    commit = ''
    author = ''
    date = ''
    message = ''

    def __init__(self):
        pass
