#!/usr/bin/env python

import os

from project.angular_project import AngularProject
from project.maven_project import MavenProject


class ProjectManagerStrategy:

    def get_instance(self, path):
        os.chdir(path)
        if os.path.exists('pom.xml'):
            return MavenProject(path)
        elif os.path.exists('package.json'):
            return AngularProject(path)
        else:
            raise NotImplementedError('Project not supported!')
