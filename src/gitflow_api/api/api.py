#!/usr/bin/env python
# encoding: utf-8

import abc
import os

from gitflow_api.api.api_merge_request import ApiMergeRequest

class Api(object):
    __metaclass__ = abc.ABCMeta

    global api_url
    global api_key
    global path

    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url

        self.path = os.getcwd()

    @abc.abstractmethod
    def get_merge_request_api(self):
        return ApiMergeRequest()
