#!/usr/bin/env python

import os

from gitflowLibs.project_management.angular_project import AngularProject
from gitflowLibs.project_management.maven_project import MavenProject

class ProjectManagementStrategy():

    def getInstance(self, path):
        os.chdir(path)
        if os.path.exists('pom.xml'):
            return MavenProject(path)
        elif os.path.exists('package.json'):
            return AngularProject(path)
        else:
            raise NotImplementedError('Project not supported!')
