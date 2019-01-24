#!/usr/bin/env python
# encoding: utf-8
import os
from enum import Enum

from gitflow_api.config.config import Config
from gitflow_api.project.project_manager_strategy import ProjectManagerStrategy
from gitflow_api.utilities.git_helper import GitHelper


class VersionUtils:

    def __init__(self):
        pass

    @staticmethod
    def get_new_version(version, version_type, is_snapshot, increment):
        splitted_version = version.split('.')

        if version_type != Version.NONE:
            version_number = int(splitted_version[len(splitted_version) - version_type.value])
            splitted_version[len(splitted_version) - version_type.value] = str(
                version_number
                + (increment if increment > 0 or version_number > 0 else 0))

        if is_snapshot:
            new_version = '.'.join(splitted_version) + '-SNAPSHOT'
        else:
            new_version = '.'.join(splitted_version)

        return new_version

    @staticmethod
    def diff_version(version1, version2):
        if VersionUtils.extract_version(version1, Version.MAJOR) > VersionUtils.extract_version(version2, Version.MAJOR):
            return 1
        elif VersionUtils.extract_version(version1, Version.MAJOR) < VersionUtils.extract_version(version2, Version.MAJOR):
            return -1
        else:
            if VersionUtils.extract_version(version1, Version.MINOR) > VersionUtils.extract_version(version2, Version.MINOR):
                return 1
            elif VersionUtils.extract_version(version1, Version.MINOR) < VersionUtils.extract_version(version2, Version.MINOR):
                return -1
            else:
                if VersionUtils.extract_version(version1, Version.PATCH) > VersionUtils.extract_version(version2, Version.PATCH):
                    return 1
                elif VersionUtils.extract_version(version1, Version.PATCH) < VersionUtils.extract_version(version2, Version.PATCH):
                    return -1
                else:
                    return 0

    @staticmethod
    def extract_version(version, version_type):
        try:
            splitted_version = version.replace('-SNAPSHOT', '').split('.')
            return int(splitted_version[len(splitted_version) - version_type.value])
        except Exception as e:
            return -1

    @staticmethod
    def adjust_versions():
        config = Config()
        project = ProjectManagerStrategy.get_instance(os.getcwd())

        git = GitHelper()

        git.checkout_and_pull(config.master_branch)
        master_version = project.actual_version()

        incremented_version = VersionUtils.get_new_version(master_version, Version.MINOR, True, 1)

        new_version = '{}.{}.0'.format(VersionUtils.extract_version(incremented_version, Version.MAJOR), VersionUtils.extract_version(incremented_version, Version.MINOR))

        git.checkout_and_pull(config.staging_branch)
        project.update_version(new_version)

        git.commit_and_push_update_message(config.staging_branch, new_version)


class Version(Enum):
    NONE = 0
    PATCH = 1
    MINOR = 2
    MAJOR = 3
