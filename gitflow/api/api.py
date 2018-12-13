#!/usr/bin/env python
# encoding: utf-8

import abc
import os

from gitflow.api.api_merge_request import ApiMergeRequest
from gitflow.api.api_project import ApiProject


class Api(object):
    __metaclass__ = abc.ABCMeta

    global api_url
    global api_key
    global path

    def __init__(self, api_key, api_url):
        if api_key is not None and api_url is not None:
            self.api_key = api_key
            self.api_url = api_url
        else:
            self.api_key = os.environ['GITFLOW_API_KEY']
            self.api_url = os.environ['GITFLOW_API_URL']

        self.path = os.getcwd()

    @abc.abstractmethod
    def get_merge_request_api(self):
        return ApiMergeRequest()

    @abc.abstractmethod
    def get_project_api(self):
        return ApiProject()
