#!/usr/bin/env python
from subprocess import check_call

from gitflowLibs.project_management.project_management import ProjectManagement, Dependency

from xml.etree import ElementTree

import json
import os


class MavenProject(ProjectManagement):
	global namespaces

	def __init__(self, path):
		self.namespaces = {'xmlns': 'http://maven.apache.org/POM/4.0.0'}
		super(MavenProject, self).__init__(path)

	def actualVersion(self):
		return self._getActualVersion()

	def updateVersion(self, version):
		mvn_cmd = 'mvn versions:set -DnewVersion={}'.format(version)
		check_call(mvn_cmd, shell=True)

		os.remove("pom.xml.versionsBackup")

	def updateDependenciesVersion(self):
		mvn_cmd = 'mvn versions:use-releases -Dmessage="update from snapshot to release" scm:checkin -f {}/pom.xml'.format(
			self.path)
		check_call(mvn_cmd, shell=True)


	def dependencies(self):
		return self._getDependenciesFromPath()


	def test(self):
		mvn_cmd = 'mvn -B clean test'
		check_call(mvn_cmd, shell=True)


	def deploy(self):
		mvn_cmd = 'mvn -B deploy -DskipTests'
		check_call(mvn_cmd, shell=True)


	def _getDependenciesFromPath(self):
		tree = ElementTree.parse(self.path + "/" + "pom.xml")
		root = tree.getroot()

		# Get dependencies for root
		dependencies = []
		dependencies.extend(self._getSnapshotDependenciesFromXml(root))

		# Get dependencies for submodules
		modules = root.findall(".//xmlns:modules", namespaces=self.namespaces)
		for module in modules:
			moduleList = module.findall("xmlns:module", namespaces=self.namespaces)

			for moduleName in moduleList:
				tree = ElementTree.parse(self.path + "/" + moduleName.text + "/pom.xml")
				dependencies.extend(self._getSnapshotDependenciesFromXml(tree.getroot()))

		return self._groupAndOrderDependencies(dependencies)


	def _getActualVersion(self):
		tree = ElementTree.parse(self.path + "/" + "pom.xml")
		root = tree.getroot()
		return str(root.find("xmlns:version", namespaces=self.namespaces).text)


	def _getSnapshotDependenciesFromXml(self, root):
		dependencies = []
		deps = root.findall(".//xmlns:dependency", namespaces=self.namespaces)
		for d in deps:
			groupId = d.find("xmlns:groupId", namespaces=self.namespaces)
			artifactId = d.find("xmlns:artifactId", namespaces=self.namespaces)
			version = d.find("xmlns:version", namespaces=self.namespaces)

			if artifactId is None \
					or version is None \
					or groupId is None:
				continue

			if str(version.text).find('SNAPSHOT') >= 0:
				dependency = Dependency(str(groupId.text), str(artifactId.text), '', str(version.text))
				dependencies.append(dependency)

		return dependencies


	def _groupAndOrderDependencies(self, dependencies):
		projectsGroup = []
		projectsGroup.append(Dependency('br.tur.reservafacil.soa', 'adapters', 'rf-adapters', '10'))
		projectsGroup.append(Dependency('br.tur.reservafacil.soa', 'dominio', 'rf-dominio', '20'))
		projectsGroup.append(Dependency('br.tur.reservafacil.soa', 'canonico', 'rf-canonico-aereo', '20'))

		groupedDependencies = []

		for dependency in dependencies:
			filteredProjectGroup = list(
				filter(lambda x: dependency.artifactId.find(x.artifactId) != -1 and dependency.groupId == x.groupId,
					   projectsGroup))

			if len(filteredProjectGroup) > 0:
				dependency.artifactId = filteredProjectGroup[0].groupName

			if len(list(filter(lambda x: dependency.artifactId.find(x.artifactId) != -1 and dependency.groupId == x.groupId,
							   groupedDependencies))) == 0:
				groupedDependencies.append(dependency)

		return groupedDependencies


	def _jsonToObject(self, data):
		return json.loads(data, object_hook=lambda d: Namespace(**d))
