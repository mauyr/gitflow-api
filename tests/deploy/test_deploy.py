#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase, mock
from unittest.mock import patch

from gitflow_api.config.config import Config
from gitflow_api.deploy.deploy_strategy import DeployStrategy


class TestDeploy(TestCase):

    @staticmethod
    def fake_config():
        config = Config()
        config.extension_deploy_class = 'Maven'
        return config

    @staticmethod
    def fake_config_without_deploy_class():
        config = Config()
        return config

    @patch.object(DeployStrategy, '_get_config', fake_config)
    def test_get_configured_instance(self):
        instance = DeployStrategy.get_instance('Pypi')
        self.assertTrue(instance.__qualname__ == 'Maven')

    @patch.object(DeployStrategy, '_get_config', fake_config_without_deploy_class)
    def test_get_pypi_instance(self):
        instance = DeployStrategy.get_instance('Pypi')
        self.assertTrue(instance.__qualname__ == 'Pypi')
