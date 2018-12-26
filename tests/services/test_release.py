#!/usr/bin/env python
# encoding: utf-8

import configparser
import os
from configparser import ConfigParser
from unittest import TestCase
from unittest.mock import patch

from gitflow_api.config.properties import VERSION
from gitflow_api.services.changelog import Changelog
from gitflow_api.services.release import Release


class TestRelease(TestCase):

    @staticmethod
    def fake_changelog(branch):
        return '# Melhorias\n* (Teste)[Teste]'

    @staticmethod
    def fake_read_config():
        config = configparser.ConfigParser()
        config.read('mock/gitflow.config.mock')
        return config

    @patch.object(Changelog, 'create_changelog', fake_changelog)
    @patch.object(Release, '_read_config_file', fake_read_config)
    def test__create_and_write_changelog(self):
        project_name = 'projectTest'
        version = '1.0.0'
        Release()._create_and_write_changelog(project_name, version)

        #assertion
        config = TestRelease.fake_read_config()
        filename = VERSION.format(project_name, version)
        path = config['CHANGELOG']['path']
        file = open(path + './' + filename, 'r')
        self.assertTrue(''.join(file.readlines()) == TestRelease.fake_changelog('branch'))

        os.remove(path + './' + filename)
        os.removedirs(path)
