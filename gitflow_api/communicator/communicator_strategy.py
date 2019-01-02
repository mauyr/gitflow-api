#!/usr/bin/env python
# encoding: utf-8
import configparser
import os

from gitflow_api.communicator.communicator import CommunicatorType
from gitflow_api.communicator.slack import Slack
from gitflow_api.config.properties import CONFIG_FILE


class CommunicatorStrategy:

    @staticmethod
    def get_instance():
        config = configparser.ConfigParser()
        if os.path.exists(CONFIG_FILE):
            config.read(CONFIG_FILE)
            communicator_type = str(config['COMMUNICATOR']['type']).lower()
            post_updates = bool(config['COMMUNICATOR']['post_updates'])
            communicator_release_webhook = str(config['COMMUNICATOR']['release_webhook']).lower() if config['COMMUNICATOR']['release_webhook'] is not None else os.environ['GITFLOW_COMMUNICATOR_RELEASE']
            communicator_launch_webhook = str(config['COMMUNICATOR']['launch_webhook']).lower() if config['COMMUNICATOR']['launch_webhook'] is not None else os.environ['GITFLOW_COMMUNICATOR_LAUNCH']

            if communicator_type == CommunicatorType.SLACK.value and post_updates:
                return Slack(communicator_release_webhook,communicator_launch_webhook)
            elif not post_updates:
                raise ModuleNotFoundError('Communicator not configured!')
            else:
                raise NotImplementedError('Communicator not supported!')
        else:
            raise ModuleNotFoundError('Communicator not configured!')
