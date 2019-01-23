#!/usr/bin/env python
# encoding: utf-8
import json
from unittest import TestCase
from unittest.mock import patch

import os

from gitflow_api.project.angular_project import AngularProject


class TestAngularProject(TestCase):

    @staticmethod
    def get_correct_package_file():
        return 'project/mock/package.json.mock'

    @patch.object(AngularProject, '_get_version_filename', get_correct_package_file)
    def test_actual_version_with_correct_setup(self):
        angular_project = AngularProject(os.path)
        actual_version = angular_project.actual_version()
        self.assertEqual(actual_version, '1.0.0')

    @staticmethod
    def write_fake_package(data, filename):
        return data

    @patch.object(AngularProject, '_get_version_filename', get_correct_package_file)
    @patch.object(AngularProject, '_write_new_version', write_fake_package)
    def test_update_version(self):
        angular_project = AngularProject(os.path)
        new_file = angular_project.update_version('2.0.0')

        self.assertTrue(new_file["version"] == "2.0.0")
