#!/usr/bin/env python
# encoding: utf-8

from subprocess import check_call

from gitflow_api.deploy.deploy_strategy import DeployStrategy
from gitflow_api.project.project_manager import ProjectManager, Dependency

from xml.etree import ElementTree

import json
import os


class MavenProject(ProjectManager):
    global namespaces

    def __init__(self, path):
        self.namespaces = {'xmlns': 'http://maven.apache.org/POM/4.0.0'}
        super(MavenProject, self).__init__(path)

    def actual_version(self):
        return self._get_actual_version()

    def update_version(self, version):
        mvn_cmd = 'mvn versions:set -DnewVersion={}'.format(version)
        check_call(mvn_cmd, shell=True)

        try:
            os.remove("pom.xml.versionsBackup")
        except Exception as e:
            pass

    def update_dependencies_version(self):
        mvn_cmd = 'mvn versions:use-releases -Dmessage="update from snapshot to release" scm:checkin -f {}/pom.xml'.format(
            self.path)
        check_call(mvn_cmd, shell=True)

    def dependencies(self):
        return self._get_dependencies_from_path()

    def test(self):
        mvn_cmd = 'mvn -B clean test'
        check_call(mvn_cmd, shell=True)

    def deploy_local(self):
        mvn_cmd = 'mvn -B deploy -DskipTests'
        check_call(mvn_cmd, shell=True)

    def deploy(self):
        DeployStrategy.get_instance(default_deploy_class='gitflow_api.deploy.maven.Maven').deploy()

    def _get_dependencies_from_path(self):
        tree = ElementTree.parse(self.path + "/" + "pom.xml")
        root = tree.getroot()

        # Get dependencies for root
        dependencies = []
        dependencies.extend(self._get_snapshot_dependencies_from_xml(root))

        # Get dependencies for submodules
        modules = root.findall(".//xmlns:modules", namespaces=self.namespaces)
        for module in modules:
            moduleList = module.findall("xmlns:module", namespaces=self.namespaces)

            for moduleName in moduleList:
                tree = ElementTree.parse(self.path + "/" + moduleName.text + "/pom.xml")
                dependencies.extend(self._get_snapshot_dependencies_from_xml(tree.getroot()))

        return self._group_and_order_dependencies(dependencies)

    def _get_actual_version(self):
        tree = ElementTree.parse(self.path + "/" + "pom.xml")
        root = tree.getroot()
        return str(root.find("xmlns:version", namespaces=self.namespaces).text)

    def _get_snapshot_dependencies_from_xml(self, root):
        dependencies = []
        deps = root.findall(".//xmlns:dependency", namespaces=self.namespaces)
        for d in deps:
            group_id = d.find("xmlns:groupId", namespaces=self.namespaces)
            artifact_id = d.find("xmlns:artifactId", namespaces=self.namespaces)
            version = d.find("xmlns:version", namespaces=self.namespaces)

            if artifact_id is None \
                    or version is None \
                    or group_id is None:
                continue

            if str(version.text).find('SNAPSHOT') >= 0:
                dependency = Dependency(str(group_id.text), str(artifact_id.text), '', str(version.text))
                dependencies.append(dependency)

        return dependencies

    def _group_and_order_dependencies(self, dependencies):
        projects_group = [Dependency('br.tur.reservafacil.soa', 'adapters', 'rf-adapters', '10'),
                          Dependency('br.tur.reservafacil.soa', 'dominio', 'rf-dominio', '20'),
                          Dependency('br.tur.reservafacil.soa', 'canonico', 'rf-canonico-aereo', '20')]

        grouped_dependencies = []

        for dependency in dependencies:
            filtered_project_group = list(
                filter(lambda x: dependency.artifactId.find(x.artifactId) != -1 and dependency.groupId == x.groupId,
                       projects_group))

            if len(filtered_project_group) > 0:
                dependency.artifactId = filtered_project_group[0].groupName

            if len(list(
                    filter(lambda x: dependency.artifactId.find(x.artifactId) != -1 and dependency.groupId == x.groupId,
                           grouped_dependencies))) == 0:
                grouped_dependencies.append(dependency)

        return grouped_dependencies

    def _json_to_object(self, data):
        return json.loads(data, object_hook=lambda d: Namespace(**d))
