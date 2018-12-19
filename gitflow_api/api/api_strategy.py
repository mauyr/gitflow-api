#!/usr/bin/env python
# encoding: utf-8

import configparser
import os
from enum import Enum

from gitflow_api.api.gitlab_manager.gitlab_manager import GitlabManager
from gitflow_api.config.properties import CONFIG_FILE
from gitflow_api.utilities.git_helper import GitHelper


class ApiStrategy:
    API_NOT_SUPPORTED = 'Api not supported!'

    @staticmethod
    def get_instance(path):
        os.chdir(path)
        api_type = os.environ['GITFLOW_API_TYPE']

        if os.path.exists(CONFIG_FILE):
            return ApiStrategy._get_api_by_config_file(CONFIG_FILE)

        elif api_type is not None:
            return ApiStrategy._get_api_by_environment(api_type)

        else:
            return ApiStrategy._get_api_by_url()

    @staticmethod
    def _get_api_by_url():
        url = str(GitHelper().get_current_url()).lower()
        if url.find(ApiType.GITLAB.value) >= 0:
            return GitlabManager(None, None)
        elif url.find(ApiType.GITHUB.value) >= 0:
            return None

        raise NotImplementedError(ApiStrategy.API_NOT_SUPPORTED)

    @staticmethod
    def _get_api_by_environment(api_type):
        if api_type == ApiType.GITLAB.value:
            return GitlabManager(None, None)
        elif api_type == ApiType.GITHUB.value:
            return None

        raise NotImplementedError(ApiStrategy.API_NOT_SUPPORTED)

    @staticmethod
    def _get_api_by_config_file(gitflow_config_file):
        config = configparser.ConfigParser()
        config.read(gitflow_config_file)
        api_type = str(config['API']['type']).lower()
        api_key = str(config['API']['key'])
        api_url = str(config['API']['url'])
        if api_type == ApiType.GITLAB.value:
            return GitlabManager(api_key, api_url)
        elif api_type == ApiType.GITHUB.value:
            return None

        raise NotImplementedError(ApiStrategy.API_NOT_SUPPORTED)


class ApiType(Enum):
    GITLAB = "gitlab"
    GITHUB = "github"
