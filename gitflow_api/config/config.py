#!/usr/bin/env python
# encoding: utf-8
import configparser
import os

from gitflow_api.config.properties import *


class Config:
    # Branches structure
    master_branch = ''
    staging_branch = ''

    hotfix_branch = ''
    feature_branch = ''
    release_branch = ''

    version = ''

    # Issue Classification - Api Labels
    feature_labels = []
    change_labels = []
    bug_labels = []
    technical_debt_labels = []
    ignore_labels = []

    version_label_prefix = ''

    # Api Config
    api_type = None
    api_key = ''
    api_url = ''

    # Communicator Config
    communicator_type = None
    communicator_release_webhook = ''
    communicator_launch_webhook = ''

    # Changelog
    changelog_create_file = False
    changelog_path = ''

    # Extension
    extension_deploy_class = None

    # Config file instance
    config_file = None

    def __init__(self):
        self.config_file = configparser.ConfigParser()
        self.config_file.read(CONFIG_FILE)

        self._set_properties()
        self._set_api_config()
        self._set_communicator_config()
        self._set_changelog_config()

    # Method for mock tests
    def get_config_file(self):
        return self.config_file

    def _set_properties(self):
        self.master_branch = self._get_property('PROPERTIES', 'master_branch', DEFAULT_MASTER_BRANCH)
        self.staging_branch = self._get_property('PROPERTIES', 'staging_branch', DEFAULT_STAGING_BRANCH)
        self.hotfix_branch = self._get_property('PROPERTIES', 'hotfix_branch', DEFAULT_HOTFIX_BRANCH)
        self.feature_branch = self._get_property('PROPERTIES', 'feature_branch', DEFAULT_FEATURE_BRANCH)
        self.release_branch = self._get_property('PROPERTIES', 'release_branch', DEFAULT_RELEASE_BRANCH)
        self.version = self._get_property('PROPERTIES', 'version', DEFAULT_VERSION)
        self.feature_labels = self._get_property('PROPERTIES', 'feature_labels', DEFAULT_FEATURE_LABELS)
        self.change_labels = self._get_property('PROPERTIES', 'change_labels', DEFAULT_CHANGE_LABELS)
        self.bug_labels = self._get_property('PROPERTIES', 'bug_labels', DEFAULT_BUG_LABELS)
        self.technical_debt_labels = self._get_property('PROPERTIES', 'technical_debt_labels', DEFAULT_TECHNICAL_DEBT_LABELS)
        self.ignore_labels = self._get_property('PROPERTIES', 'ignore_labels', DEFAULT_IGNORE_LABELS)
        self.version_label_prefix = self._get_property('PROPERTIES', 'version_label_prefix', DEFAULT_VERSION_LABEL_PREFIX)

    def _set_api_config(self):
        self.api_type = str(self._get_config_or_environment('API', 'type', 'GITFLOW_API_TYPE', None)).lower()
        self.api_key = self._get_config_or_environment('API', 'key', 'GITFLOW_API_KEY', '')
        self.api_url = self._get_config_or_environment('API', 'url', 'GITFLOW_API_URL', '')

    def _set_changelog_config(self):
        self.changelog_create_file = bool(self._get_property('CHANGELOG', 'create_file', False))
        self.changelog_path = self._get_property('CHANGELOG', 'path', '')

    def _set_communicator_config(self):
        self.communicator_type = str(self._get_config_or_environment('COMMUNICATOR', 'type', 'GITFLOW_COMMUNICATOR_TYPE', 'None')).lower()
        self.communicator_release_webhook = str(self._get_config_or_environment('COMMUNICATOR', 'release_webhook', 'GITFLOW_COMMUNICATOR_RELEASE', ''))
        self.communicator_launch_webhook = str(self._get_config_or_environment('COMMUNICATOR', 'launch_webhook', 'GITFLOW_COMMUNICATOR_LAUNCH', ''))

    def _set_extension(self):
        self.extension_deploy_class = self._get_property('EXTENSION', 'deploy_class', None)

    def _get_config_or_environment(self, group, api_config, os_environment, default_value):
        try:
            return self.config_file[group][api_config]
        except Exception as e:
            try:
                return os.environ[os_environment]
            except Exception as ex:
                return default_value

    def _get_property(self, group, config_property, default_property):
        try:
            return self.config_file[group][config_property]
        except Exception as e:
            return default_property
