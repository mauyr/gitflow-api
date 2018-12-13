#!/usr/bin/env python

import abc


class ProjectManager(object):
    __metaclass__ = abc.ABCMeta

    global path

    def __init__(self, path):
        self.path = str(path)

    @abc.abstractmethod
    def actual_version(self):
        return

    @abc.abstractmethod
    def update_version(self, version):
        return

    @abc.abstractmethod
    def update_dependencies_version(self):
        pass

    @abc.abstractmethod
    def dependencies(self):
        return

    @abc.abstractmethod
    def test(self):
        pass

    @abc.abstractmethod
    def deploy(self):
        pass


class Dependency(object):
    groupId = ''
    artifactId = ''
    groupName = ''
    version = ''

    # The class "constructor" - It's actually an initializer
    def __init__(self, groupId, artifactId, groupName, version):
        self.groupId = str(groupId)
        self.artifactId = str(artifactId)
        self.groupName = str(groupName)
        self.version = str(version)
