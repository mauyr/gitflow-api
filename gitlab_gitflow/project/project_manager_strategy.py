#!/usr/bin/env python

import os

from gitlab_gitflow.project.angular_project import AngularProject
from gitlab_gitflow.project.maven_project import MavenProject
from gitlab_gitflow.project.python_project import PythonProject


class ProjectManagerStrategy:

    def get_instance(self, path):
        os.chdir(path)
        if os.path.exists('pom.xml'):
            return MavenProject(path)
        elif os.path.exists('package.json'):
            return AngularProject(path)
        elif os.path.exists('setup.py'):
            return PythonProject(path)
        else:
            raise NotImplementedError('Project not supported!')
