#!/usr/bin/env python
# encoding: utf-8
from gitflow_api.config.config import Config
from gitflow_api.deploy.deploy import Deploy


class DeployStrategy:

    @staticmethod
    def get_instance(default_deploy_class):
        config = DeployStrategy._get_config()
        if config.extension_deploy_class is not None:
            package, classname = DeployStrategy.extract_package_and_classname(config.extension_deploy_class)
        else:
            package, classname = DeployStrategy.extract_package_and_classname(default_deploy_class)

        exec('from {} import {}'.format(package, classname))
        return eval('{}()'.format(classname))

    @staticmethod
    def extract_package_and_classname(fullname):
        last_dot = fullname.rfind('.')
        return fullname[:last_dot], fullname[last_dot+1:]

    @staticmethod
    def _get_config():
        return Config()