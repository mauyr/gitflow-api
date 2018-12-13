#!/usr/bin/env python
import abc


class ApiProject(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractmethod
    def find_project_by_url(self, url):
        return
