#!/usr/bin/env python
# encoding: utf-8

import os
from enum import Enum

from gitflow_api.api.gitlab_manager.gitlab_manager import GitlabManager
from gitflow_api.config.config import Config


class ApiStrategy:
    API_NOT_SUPPORTED = 'Api not supported!'

    @staticmethod
    def get_instance(path):
        os.chdir(path)
        config = Config()

        if config.api_type == ApiType.GITLAB.value:
            return GitlabManager(config.api_key, config.api_url)
        elif config.api_type == ApiType.GITHUB.value:
            return None

        raise NotImplementedError(ApiStrategy.API_NOT_SUPPORTED)


class ApiType(Enum):
    GITLAB = "gitlab"
    GITHUB = "github"
