#!/usr/bin/env python
# encoding: utf-8
from subprocess import check_call

from gitflow_api.deploy.deploy import Deploy


class Maven(Deploy):

    def __init__(self):
        super(Maven, self).__init__()

    def deploy(self):
        mvn_cmd = 'mvn -B deploy -DskipTests'
        check_call(mvn_cmd, shell=True)
