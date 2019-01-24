#!/usr/bin/env python
# encoding: utf-8
import json
import os

from gitflow_api.api.api_strategy import ApiStrategy
from gitflow_api.config.config import Config
from gitflow_api.utilities.git_helper import GitHelper
from gitflow_api.project.project_manager_strategy import ProjectManagerStrategy
from gitflow_api.utilities.version_utils import VersionUtils, Version

STORY_TYPE = 'story'
BUG_TYPE = 'bug'
TECHNICAL_TYPE = 'technical_debt'
OTHER_TYPE = 'other'
IGNORE_TYPE = 'ignore'


class Changelog:
    config = None

    def __init__(self):
        pass

    def create_changelog(self, branch, from_tag=None, path=None, only_staging=False):
        git = GitHelper()
        branch = str(git.get_current_branch() if branch is None else branch)

        return self._create_changelog(branch, from_tag=from_tag, path=path, only_staging=only_staging)

    def create_markdown_changelog(self, branch, from_tag=None, path=None, only_staging=False, write_changelog=False):
        changelog_issues = self.create_changelog(branch, from_tag=from_tag, path=path, only_staging=only_staging)

        changelog_md = self.make_changelog_md(changelog_issues)

        if write_changelog:
            self.write_changelog(changelog_issues)

        return changelog_md

    def write_changelog(self, changelog_issues):
        if bool(self._get_config().changelog_create_file):
            git = GitHelper()
            group_name, project_name = GitHelper.extract_group_and_project_from_url(git.get_current_url())

            filename = self._get_config().version.format(project_name, version)

            path = self._get_config().changelog_path
            if not os.path.exists(path):
                os.makedirs(path)

            changelog_json = json.dumps(changelog_issues, sort_keys=True, indent=4, cls=ComplexEncoder, ensure_ascii=False)

            release_notes = open(path + './' + filename, 'w', encoding='utf8')
            release_notes.write(changelog_json)
            release_notes.close()

    def _create_changelog(self, branch, from_tag=None, path=None, only_staging=False):

        if path is not None:
            os.chdir(path)

        git = GitHelper()
        git.checkout_and_pull(branch)

        if len(git.repo.tags) == 0:
            return ChangelogIssues()

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

        group_name, project_name = GitHelper.extract_group_and_project_from_url(git.get_current_url())

        project = ProjectManagerStrategy().get_instance(os.getcwd())
        version = project.actual_version()

        changelog_issues = self._normalize_issues(group_name, project_name, commits, only_staging)
        changelog_issues.version = version
        return changelog_issues

    def _find_last_tag(self, project_name, tags):
        path = os.getcwd()

        project_management = ProjectManagerStrategy.get_instance(path)
        actual_version = project_management.actual_version().replace('-SNAPSHOT', '')
        # ultima tag
        tag_commit = tags[0]
        tag_version = str(tag_commit).replace(self._get_config().version.format(project_name, ''), '')

        if VersionUtils.extract_version(tag_version, Version.MAJOR) != VersionUtils.extract_version(
                actual_version, Version.MAJOR):
            last_version = '{}.0.0'.format(VersionUtils.extract_version(actual_version, Version.MAJOR) - 1)
            for tag in tags:
                tag_commit = tag
                tag_version = str(tag_commit).replace(self._get_config().version.format(project_name, ''), '')

                if VersionUtils.diff_version(tag_version, last_version) <= 0:
                    break
        else:

            if VersionUtils.extract_version(tag_version, Version.MINOR) != VersionUtils.extract_version(
                    actual_version, Version.MINOR):
                last_version = '{}.{}.0'.format(VersionUtils.extract_version(actual_version, Version.MAJOR),
                                                VersionUtils.extract_version(actual_version, Version.MINOR) - 1)
                for tag in tags:
                    tag_commit = tag
                    tag_version = str(tag_commit).replace(self._get_config().version.format(project_name, ''), '')

                    if VersionUtils.diff_version(tag_version, last_version) <= 0:
                        break

        return tag_commit

    def _normalize_issues(self, group_name, project_name, commits, only_staging):
        api = ApiStrategy.get_instance(os.getcwd())
        changelog_issues = ChangelogIssues()

        for commit in commits:
            # print(commit.commit)
            # print(commit.message)

            message = commit.message
            if message.find('See merge request') >= 0:

                merge_request = api.get_merge_request_api().find_merge_request_by_commit_message(group_name,
                                                                                                 project_name, message)

                add_changelog = merge_request.source_branch.find(self._get_config().release_branch.format('')) == -1
                add_changelog = add_changelog and (
                        merge_request.target_branch == self._get_config().staging_branch or not only_staging)
                add_changelog = add_changelog and merge_request.state == 'merged'
                if add_changelog:
                    issue = Issue(merge_request.title, merge_request.web_url,
                                  merge_request.labels, self._get_config())
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
            line = str(logLine)
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

    @staticmethod
    def make_changelog_md(changelog_issues):
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

    def _get_config(self):
        if (self.config is None):
            self.config = Config()

        return self.config


class ChangelogIssues:
    version = '0.0.0'
    stories = []
    bugs = []
    technicalDebts = []
    others = []

    def __init__(self):
        pass

    def toJSON(self):
        return dict(version=self.version, stories=self.stories, bugs=self.bugs, technicalDebts=self.technicalDebts, others=self.others)


class Issue:
    title = ''
    url = ''
    issueType = ''

    def __init__(self, title, url, labels, config):
        self.title = str(title)
        self.url = str(url)
        self.issueType = self._getIssueType(labels, config)

    def _getIssueType(self, labels, config):
        if len(list(filter(lambda x: str(x).find(config.version_label_prefix.format('')) == 0,
                           labels))) > 0 or len(set(config.ignore_labels) & set(labels)) > 0:
            return IGNORE_TYPE
        elif len(set(config.feature_labels) & set(labels)) > 0:
            return STORY_TYPE
        elif len(set(config.bug_labels) & set(labels)) > 0:
            return BUG_TYPE
        elif len(set(config.technical_debt_labels) & set(labels)) > 0:
            return TECHNICAL_TYPE
        else:
            return OTHER_TYPE

    def toJSON(self):
        return dict(title=self.title, url=self.url, issueType=self.issueType)


class Commit:
    commit = ''
    author = ''
    date = ''
    message = ''

    def __init__(self):
        pass


class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'toJSON'):
            return obj.toJSON()
        else:
            return json.JSONEncoder.default(self, obj)
