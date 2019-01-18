#!/usr/bin/env python
# encoding: utf-8
import configparser

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

    def __init__(self):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        self.master_branch = self.get_property(config, 'master_branch', DEFAULT_MASTER_BRANCH)
        self.staging_branch = self.get_property(config, 'staging_branch', DEFAULT_STAGING_BRANCH)

        self.hotfix_branch = self.get_property(config, 'hotfix_branch', DEFAULT_HOTFIX_BRANCH)
        self.feature_branch = self.get_property(config, 'feature_branch', DEFAULT_FEATURE_BRANCH)
        self.release_branch = self.get_property(config, 'release_branch', DEFAULT_RELEASE_BRANCH)

        self.version = self.get_property(config, 'version', DEFAULT_VERSION)

        self.feature_labels = self.get_property(config, 'feature_labels', DEFAULT_FEATURE_LABELS)
        self.change_labels = self.get_property(config, 'change_labels', DEFAULT_CHANGE_LABELS)
        self.bug_labels = self.get_property(config, 'bug_labels', DEFAULT_BUG_LABELS)
        self.technical_debt_labels = self.get_property(config, 'technical_debt_labels', DEFAULT_TECHNICAL_DEBT_LABELS)
        self.ignore_labels = self.get_property(config, 'ignore_labels', DEFAULT_IGNORE_LABELS)

        self.version_label_prefix = self.get_property(config, 'version_label_prefix', DEFAULT_VERSION_LABEL_PREFIX)

    def get_property(self, config, config_property, default_property):
        try:
            return config['PROPERTIES'][config_property]
        except Exception as e:
            return default_property
