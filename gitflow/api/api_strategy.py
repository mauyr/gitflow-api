#!/usr/bin/env python
import configparser
import os

from gitlab_gitflow.api.gitlab_manager.gitlab_manager import GitlabManager
from gitlab_gitflow.utilities.git_helper import GitHelper


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

