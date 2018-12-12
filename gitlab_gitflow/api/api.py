#!/usr/bin/env python
import abc


class Api(object):
    __metaclass__ = abc.ABCMeta

    global api_url
    global merge_request
    global project

    def __init__(self, api_url, merge_request, project):
        self.api_url = api_url
        self.merge_request = merge_request
        self.project = project

    @abc.abstractmethod
    def get_merge_request(self):
        return

    @abc.abstractmethod
    def get_project(self):
        return
