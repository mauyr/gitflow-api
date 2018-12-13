#!/usr/bin/env python
# encoding: utf-8

from subprocess import check_call

from gitflow_api.project.project_manager import ProjectManager

import re
import shutil


class PythonProject(ProjectManager):

    def __init__(self, path):
        super().__init__(path)

    def update_dependencies_version(self):
        pass

    def actual_version(self):
        lines = self._read_all_version_file()

        for line in lines:
            if str(line).lower().find('version=') >= 0:
                version = re.search('(?:(\d+)\.)?(?:(\d+)\.)?(?:(\d+)\.\d+)', str(line))
                if version is None:
                    raise ValueError('Version has incorrect format')
                return version.group(0)

        raise ValueError('Version tag not found')

    def update_version(self, version):
        lines = self._read_all_version_file()

        i = 0
        while i < len(lines):
            version_position = str(lines[i]).lower().find('version="')
            if version_position >= 0:
                lines[i] = lines[i][:version_position+9] + str(version) + '",\n'

            i += 1

        self._write_new_version(lines, self._get_version_filename())

        return lines

    def _read_all_version_file(self):
        version_file = open(self._get_version_filename(), 'r')
        lines = version_file.readlines()
        version_file.close()
        return lines

    def dependencies(self):
        return

    def test(self):
        #python -m unittest discover -s tests
        pass

    def deploy(self):
        #remove dist and build files
        shutil.rmtree('dist')
        shutil.rmtree('build')

        cmd = 'python setup.py sdist bdist_wheel'
        check_call(cmd, shell=True)

        cmd = 'twine upload dist/*'
        check_call(cmd, shell=True)

    @staticmethod
    def _get_version_filename():
        return 'setup.py'

    @staticmethod
    def _write_new_version(lines, version_filename):
        version_file = open(version_filename, 'w')
        version_file.write(''.join(lines))
        version_file.close()