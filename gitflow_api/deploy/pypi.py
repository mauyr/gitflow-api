#!/usr/bin/env python
# encoding: utf-8
import shutil
from subprocess import check_call

from gitflow_api.deploy.deploy import Deploy


class Pypi(Deploy):

    def __init__(self):
        super(Pypi, self).__init__(Pypi.__class__)
        self.__qualname__ = 'Pypi'

    def deploy(self):
        # remove dist and build files
        shutil.rmtree('dist')
        shutil.rmtree('build')

        cmd = 'python setup.py sdist bdist_wheel'
        check_call(cmd, shell=True)

        cmd = 'twine upload dist/*'
        check_call(cmd, shell=True)
