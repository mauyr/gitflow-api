#!/usr/bin/env python
import abc


class ApiMergeRequest(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractmethod
    def find_merge_request_by_url_and_branch(self, git_url, branch):
        return
