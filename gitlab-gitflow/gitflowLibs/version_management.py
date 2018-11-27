#!/usr/bin/env python

import os

from enum import Enum

from gitflowLibs.project_management.project_management_strategy import ProjectManagementStrategy
from properties import *

class VersionManagement:

	def __init__(self):
		pass

	##update version for next release
	@staticmethod
	def update_version(versionUpdate, isSnapshot):
		path = os.getcwd()
		projectManagement = ProjectManagementStrategy().getInstance(path)
		version = projectManagement.actualVersion().replace('-SNAPSHOT', '')

		newVersion = get_new_version(version, versionUpdate, isSnapshot, +1)

		projectManagement.updateVersion(newVersion)

		return newVersion

	@staticmethod
	def get_new_version(version, versionType, isSnapshot, increment):
		path = os.getcwd()

		splittedVersion = version.split('.')

		if (versionType != Version.NONE):
			splittedVersion[len(splittedVersion) - versionType.value] = str(int(splittedVersion[len(splittedVersion) - versionType.value]) + increment)

		if (isSnapshot):
			newVersion = '.'.join(splittedVersion) + '-SNAPSHOT'
		else:
			newVersion = '.'.join(splittedVersion)

		return newVersion

	@staticmethod
	def diff_version(self, version1, version2):
		if self._extractVersion(version1, Version.MAJOR) > self._extractVersion(version2, Version.MAJOR):
			return 1
		elif self._extractVersion(version1, Version.MAJOR) < self._extractVersion(version2, Version.MAJOR):
			return -1
		else:
			if self._extractVersion(version1, Version.MINOR) > self._extractVersion(version2, Version.MINOR):
				return 1
			elif self._extractVersion(version1, Version.MINOR) < self._extractVersion(version2, Version.MINOR):
				return -1
			else:
				if self._extractVersion(version1, Version.PATCH) > self._extractVersion(version2, Version.PATCH):
					return 1
				elif self._extractVersion(version1, Version.PATCH) < self._extractVersion(version2, Version.PATCH):
					return -1
				else:
					return 0

	@staticmethod
	def _extractVersion(self, version, versionType):
		try:
			splittedVersion = version.replace('-SNAPSHOT', '').split('.')
			return int(splittedVersion[len(splittedVersion) - versionType.value])
		except UnboundLocalError:
			return -1

class Version(Enum):
	NONE = 0
	PATCH = 1
	MINOR = 2
	MAJOR = 3
