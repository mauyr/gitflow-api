#!/usr/bin/env python

from gitflowLibs.project_management.project_management import ProjectManagement

class AngularProject(ProjectManagement):

    def __init__(self, path):
        super.__init__(path)

    def actualVersion(self):
        return

    def updateVersion(self, version):
        return

    def dependencies(self):
        return

    def test(self):
        return

    def deploy(self):
        return

