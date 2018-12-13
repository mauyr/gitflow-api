#!/usr/bin/env python
# encoding: utf-8

import configparser
import os

from gitflow_api.api.gitlab_manager.gitlab_manager import GitlabManager
from gitflow_api.utilities.git_helper import GitHelper


class ApiStrategy:

    @staticmethod
    def get_instance(path):
        os.chdir(path)
        if os.path.exists('gitflow.config'):
            config = configparser.ConfigParser()
            config.read("gitflow.config")
            api_type = str(config['API']['ApiType']).lower()
            api_key = str(config['API']['ApiKey'])
            api_url = str(config['API']['ApiUrl'])
            if api_type == 'gitlab':
                return GitlabManager(api_key, api_url)
            elif api_type == 'github':
                return None

        else:
            url = str(GitHelper().get_current_url()).lower()

            if url.find('gitlab') >= 0:
                return GitlabManager(None, None)
            elif url.find('github') >= 0:
                return None

        raise NotImplementedError('Api not supported!')

