#!/usr/bin/env python
# encoding: utf-8

import abc
import os
from enum import Enum

from gitflow_api.api.api_merge_request import ApiMergeRequest


class Communicator(object):
    __metaclass__ = abc.ABCMeta

    release_webhook = ''
    launch_webhook = ''

    def __init__(self, release_webhook, launch_webhook):
        self.release_webhook = release_webhook
        self.launch_webhook = launch_webhook

    @abc.abstractmethod
    def send_message(self, message, channel, project_name):
        pass

    @abc.abstractmethod
    def send_changelog(self, changelog, channel, project_name):
        pass


class CommunicatorType(Enum):
    SLACK = "slack"
