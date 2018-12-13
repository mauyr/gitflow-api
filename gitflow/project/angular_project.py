#!/usr/bin/env python
# encoding: utf-8

from gitflow.project.project_manager import ProjectManager


class AngularProject(ProjectManager):

    def __init__(self, path):
        super.__init__(path)

    def update_dependencies_version(self):
        pass

    def actual_version(self):
        return

    def update_version(self, version):
        return

    def dependencies(self):
        return

    def test(self):
        return

    def deploy(self):
        return
