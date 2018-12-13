#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase
from unittest.mock import patch

from gitflow.project.python_project import PythonProject
import os


class TestPythonProject(TestCase):

    @staticmethod
    def get_correct_setup_file():
        return 'mock/setup.py.mock'

    @patch.object(PythonProject, '_get_version_filename', get_correct_setup_file)
    def test_actual_version_with_correct_setup(self):
        python_project = PythonProject(os.path)
        actual_version = python_project.actual_version()
        self.assertEqual(actual_version, '1.0.0')

    @staticmethod
    def get_incorrect_version_setup_file():
        return 'mock/incorrect_version_setup.py.mock'

    @patch.object(PythonProject, '_get_version_filename', get_incorrect_version_setup_file)
    def test_actual_version_with_incorrect_version_setup(self):
        with self.assertRaises(ValueError) as context:
            python_project = PythonProject(os.path)
            python_project.actual_version()

        self.assertTrue('Version has incorrect format' in context.exception.args)

    @staticmethod
    def get_incorrect_setup_file():
        return 'mock/incorrect_setup.py.mock'

    @patch.object(PythonProject, '_get_version_filename', get_incorrect_setup_file)
    def test_actual_version_with_incorrect_setup(self):
        with self.assertRaises(ValueError) as context:
            python_project = PythonProject(os.path)
            python_project.actual_version()

        self.assertTrue('Version tag not found' in context.exception.args)

    @staticmethod
    def write_fake_setup(lines, version_file):
        pass

    @patch.object(PythonProject, '_get_version_filename', get_correct_setup_file)
    @patch.object(PythonProject, '_write_new_version', write_fake_setup)
    def test_update_version(self):
        python_project = PythonProject(os.path)
        new_file = python_project.update_version('2.0.0')

        self.assertTrue(len(list(filter(lambda x: str(x).find('version="2.0.0"') >= 0, new_file))) > 0)

        print(new_file)




