#!/usr/bin/env python
import abc
import os


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
    def get_merge_request(self):
        return

    @abc.abstractmethod
    def get_project(self):
        return
