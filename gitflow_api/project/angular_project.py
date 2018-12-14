#!/usr/bin/env python
# encoding: utf-8
import json

from gitflow_api.project.project_manager import ProjectManager


class AngularProject(ProjectManager):

    def __init__(self, path):
        super().__init__(path)

    def update_dependencies_version(self):
        pass

    def actual_version(self):
        with open(AngularProject._get_version_filename()) as f:
            data = json.load(f)
            return data["version"]

    def update_version(self, version):
        with open(AngularProject._get_version_filename()) as f:
            data = json.load(f)
            data["version"] = version
            return AngularProject._write_new_version(data, AngularProject._get_version_filename())

    def dependencies(self):
        return

    def test(self):
        return

    def deploy(self):
        return

    @staticmethod
    def _get_version_filename():
        return 'package.json'

    @staticmethod
    def _write_new_version(data, version_filename):
        version_file = open(version_filename, 'w')
        json.dump(data, version_file, indent=4)
        version_file.truncate()
