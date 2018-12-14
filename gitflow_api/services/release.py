#!/usr/bin/env python
# encoding: utf-8

import os

from gitflow_api.api.api_strategy import ApiStrategy
from gitflow_api.config.properties import *
from gitflow_api.utilities.git_helper import GitHelper
from gitflow_api.services.changelog import Changelog
from gitflow_api.utilities.version_utils import VersionUtils, Version
from gitflow_api.project.project_manager_strategy import ProjectManagerStrategy


class Release:

    def __init__(self):
        pass

    def release_start(self):
        git = GitHelper()

        group_name, url_pattern = self._url_pattern_build(git)

        initial_path = os.getcwd()

        git = GitHelper()
        git.get_git_cmd().checkout(STAGING_BRANCH)
        git.get_git_cmd().pull()

        git.check_conflicts(MASTER_BRANCH)

        # print(urlPattern)
        release_branch = RELEASE_BRANCH.format(self._recursive_release(initial_path, url_pattern, group_name))

        self._create_merge_requests(initial_path, release_branch)

        # Get back to initial directory
        os.chdir(initial_path)

    def release_finish(self, args):
        git = GitHelper()
        path = os.getcwd()
        os.chdir(path)

        api = ApiStrategy.get_instance(path)

        branch = str(git.get_current_branch() if args.branch is None else args.branch)

        if branch.lower().find('release') < 0:
            raise ValueError('Not valid release branch {}'.format(branch))

        # continue if dont have conflicts or merge request for release is merged
        try:
            api.get_merge_request_api().validate_and_close_merge_request(git.get_current_url(), branch)
        except RuntimeWarning as ex:
            print('Release branch merged!', ex)
        except ValueError as e:
            raise ValueError(e)

        # Synchronization merge request from master to staging to execute after finish release
        git.get_git_cmd().checkout(STAGING_BRANCH)
        git.get_git_cmd().pull()
        try:
            git.check_conflicts(MASTER_BRANCH)
        except Exception as e:
            print(e)
            api.get_merge_request_api().create_merge_request(git.get_current_url(), MASTER_BRANCH,
                                               'Synchronization merge request {} to {}'.format(MASTER_BRANCH,
                                                                                               STAGING_BRANCH),
                                               'Don\'t remove this merge request before finish release', None,
                                               STAGING_BRANCH, None)
            api.get_merge_request_api().validate_merge_request_by_url_and_branches(git.get_current_url(), MASTER_BRANCH,
                                                                     STAGING_BRANCH)

        git.get_git_cmd().pull()

        new_version = self._update_version(Version.MINOR, True)
        git.commit_and_push_update_message(STAGING_BRANCH, new_version)

    def launch(self):
        git = GitHelper()
        git.checkout_and_pull(MASTER_BRANCH)

        path = os.getcwd()
        project_management = ProjectManagerStrategy.get_instance(path)

        version = project_management.actual_version().replace('-SNAPSHOT', '')

        # TODO: Criar rotinas para release recursivos e verificar se todas as dependencias nao estao mais em snapshot
        project_management.update_version(version)
        project_management.update_dependencies_version()

        git.commit_and_push_update_message(MASTER_BRANCH, version)

        group_name, project_name = git.extract_group_and_project()

        # FIXME: Usar o changlog para atualizar o texto da tag no gitlab e não como commit message
        # changelog = ''
        # try:
        #     changelog = Changelog().create_changelog(MASTER_BRANCH)
        # except Exception as e:
        #     changelog = 'Changelog not generated'
        #     print("Fail to create changelog", e)

        git.create_tag(VERSION.format(project_name, version), version)

        project_management.deploy()

        # update patch version for next tag
        new_version = self._update_version(Version.PATCH, False)

        git.commit_and_push_update_message(MASTER_BRANCH, new_version)

    def _update_version(self, version_update, is_snapshot):
        path = os.getcwd()
        project_management = ProjectManagerStrategy.get_instance(path)
        version = project_management.actual_version().replace('-SNAPSHOT', '')

        new_version = VersionUtils.get_new_version(version, version_update, is_snapshot, +1)

        project_management.update_version(new_version)

        return new_version

    def _recursive_release(self, actual_path, url_pattern, origin_group_name):

        project_management = ProjectManagerStrategy.get_instance(actual_path)

        os.chdir(actual_path)

        project_management.update_dependencies_version()

        git = GitHelper()
        git.get_git_cmd().checkout(STAGING_BRANCH)
        git.get_git_cmd().pull()

        dependencies = project_management.dependencies()
        print('Total dependencies of {}: {}'.format(actual_path, len(dependencies)))

        if len(dependencies) > 0:
            for dependency in dependencies:
                path = self._checkout_dependency(STAGING_BRANCH, actual_path, dependency, origin_group_name,
                                                 url_pattern)
                try:
                    dependency_project_manager = ProjectManagerStrategy.get_instance(path)
                    os.chdir(path)
                    git = GitHelper()

                    dependency_version = dependency.version.replace('-SNAPSHOT', '')
                    git.get_git_cmd().checkout('release/' + dependency_version)

                    dependency_project_manager.deploy()
                except Exception as e:
                    self._recursive_release(path, url_pattern, origin_group_name)

        try:
            os.chdir(actual_path)

            git = GitHelper()
            release_version = project_management.actual_version().replace('-SNAPSHOT', '')

            print('Starting release of {}'.format(os.getcwd()))

            project_management.test()

            git.create_new_branch_from(STAGING_BRANCH, RELEASE_BRANCH.format(release_version))

            project_management.deploy()

            return release_version
        except RuntimeError as e:
            print('Error creating release of {}: {}'.format(os.getcwd(), str(e)))

    def _create_merge_requests(self, path, branch):
        os.chdir(path)

        git = GitHelper()
        group_name, url_pattern = self._url_pattern_build(git)

        merge_requests = self._create_recursive_merge_request(branch, path, url_pattern, group_name)

        if merge_requests is not None:
            for mergeRequest in merge_requests:
                print('Merge request created: {}'.format(mergeRequest.iid))

    def _create_recursive_merge_request(self, branch, actual_path, url_pattern, origin_group_name):
        project_management = ProjectManagerStrategy.get_instance(actual_path)

        os.chdir(actual_path)
        git = GitHelper()
        merge_requests = []

        git.get_git_cmd().checkout(branch)
        git.get_git_cmd().pull()

        dependencies = project_management.dependencies()
        print('Total dependencies of {}: {}'.format(actual_path, len(dependencies)))

        if len(dependencies) > 0:
            for dependency in dependencies:
                release_version = dependency.version.replace('-SNAPSHOT', '')
                path = self._checkout_dependency('release/' + release_version, actual_path, dependency,
                                                 origin_group_name,
                                                 url_pattern)

                merge_requests.extend(
                    self._create_recursive_merge_request('release/' + release_version, path, url_pattern,
                                                         origin_group_name))
        api = ApiStrategy.get_instance(actual_path)

        merge_request = api.get_merge_request_api().find_merge_request_by_url_and_branch(git.get_current_url(), branch)
        if merge_request is None:
            description = str('## Merge requests\n')
            for createdMergeRequests in merge_requests:
                description = description + '* ' + createdMergeRequests.web_url.encode('utf-8').strip() + '\n'

            description = description + Changelog().create_changelog(branch, path=actual_path)

            merge_requests.append(
                api.get_merge_request_api().create_merge_request(git.get_current_url(), branch,
                                                                 'Release {} - ' + branch,
                                                                 description, None, MASTER_BRANCH, None))

        return merge_requests

    def _checkout_dependency(self, branch, actual_path, dependency, origin_group_name, url_pattern):
        print('Checkout from {} dependency {}'.format(actual_path, dependency.artifactId))

        group = origin_group_name
        shared_projects = list(filter(lambda x: dependency.artifactId == x.project, self._get_shared_projects()))
        if len(shared_projects) > 0:
            group = shared_projects[0].group
        shared_projects = list(filter(lambda x: dependency.artifactId == x.project, self._get_shared_projects()))
        if len(shared_projects) > 0:
            group = shared_projects[0].group

        path = '../{}'.format(dependency.artifactId)
        if not os.path.exists(path):
            print('Cloning repository: {}'.format(url_pattern.format(group, dependency.artifactId)))
            new_repo = GitHelper()
            new_repo.repo.clone_from(url_pattern.format(group, dependency.artifactId), path)

            os.chdir(path)
            git_helper = GitHelper()
            git_helper.get_git_cmd().checkout(branch)
            git_helper.get_git_cmd().pull()

        return path

    # List of shared projects
    def _get_shared_projects(self):
        projects = [Project('rf-dominio', 'desenvolvimento'), Project('rf-adapters', 'desenvolvimento'),
                    Project('rf-canonico-aereo', 'gateway'), Project('rf-client-sabre', 'gateway')]
        return projects

    def _url_pattern_build(self, git_helper):
        url = git_helper.get_current_url().split('/')
        group_name = str(url[0][url[0].rfind(':') + 1:])
        url[0] = str(url[len(url) - 2]).replace(group_name, '{}')
        url[1] = '{}'
        url_pattern = '/'.join(url)
        return group_name, url_pattern


class Project:
    project = ''
    group = ''

    def __init__(self, project, group):
        self.project = str(project)
        self.group = str(group)
