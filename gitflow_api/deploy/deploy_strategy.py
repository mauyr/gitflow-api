#!/usr/bin/env python
# encoding: utf-8
from gitflow_api.config.config import Config
from gitflow_api.deploy.deploy import Deploy


class DeployStrategy:

    @staticmethod
    def get_instance(default_deploy_class):
        config = DeployStrategy._get_config()
        if config.extension_deploy_class is not None:
            return type(config.extension_deploy_class, (Deploy,), {})
        else:
            return type(default_deploy_class, (Deploy,), {})

    @staticmethod
    def _get_config():
        return Config()