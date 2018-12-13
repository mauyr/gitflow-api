#!/usr/bin/env python
# encoding: utf-8

import gitlab

from gitflow.api.api import Api
from gitflow.api.gitlab_manager.merge_request import MergeRequest


class GitlabManager(Api):

    def get_merge_request_api(self):
        return MergeRequest(self.gl)

    global gl

    def __init__(self, api_key, api_url):
        super(Api, self).__init__(api_key, api_url)

        self.gl = gitlab.Gitlab(self.api_url, private_token=self.api_key)
