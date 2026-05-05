#!/usr/bin/env python
# encoding: utf-8

from gitflow_api.communicator.communicator import CommunicatorType
from gitflow_api.communicator.slack import Slack
from gitflow_api.config.config import Config


class CommunicatorStrategy:

    @staticmethod
    def get_instance():
        config = CommunicatorStrategy._get_config()

        if config.communicator_type == CommunicatorType.SLACK.value:
            return Slack(config.communicator_release_webhook, config.communicator_launch_webhook)
        elif config.communicator_type is None:
            raise ModuleNotFoundError('Communicator not configured!')
        else:
            raise NotImplementedError('Communicator not supported!')

    @staticmethod
    def _get_config():
        return Config()
