#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase, mock
from unittest.mock import patch, PropertyMock

from gitflow_api.communicator.communicator_strategy import CommunicatorStrategy
from gitflow_api.communicator.slack import Slack
from gitflow_api.config.config import Config
from gitflow_api.services.changelog import Changelog, Issue, ChangelogIssues


class TestCommunicator(TestCase):

    @staticmethod
    def fake_config():
        config = Config()
        config.communicator_type = 'slack'
        config.communicator_launch_webhook = 'http://slack.com/LAUNCH'
        config.communicator_release_webhook = 'http://slack.com/RELEASE'
        return config

    @staticmethod
    def fake_changelog():
        stories = [Issue('Story 1 - Fake screen for fake app', 'http://127.0.0.1', 'story', TestCommunicator.fake_config()),
                   Issue('Story 2 - Fake feature with fake button', 'http://127.0.0.1', 'story', TestCommunicator.fake_config())]
        bugs = [Issue('Bug 1 - Fake bug fixed', 'http://127.0.0.1', 'bug', TestCommunicator.fake_config())]
        changelog = ChangelogIssues()
        changelog.stories = stories
        changelog.bugs = bugs
        changelog.version = '1.0.0'
        return changelog

    @patch.object(Changelog, '_get_config', fake_config)
    def test_make_changelog_slack_format(self):
        slack_message = Slack._make_changelog_slack_format(TestCommunicator.fake_changelog(), 'Fake Project')
        self.assertEqual(slack_message, '*Fake Project - 1.0.0*\n*Improvements*\n- <http://127.0.0.1|Story 1 - Fake screen for fake app>\n- <http://127.0.0.1|Story 2 - Fake feature with fake button>\n*Bugs*\n- <http://127.0.0.1|Bug 1 - Fake bug fixed>')

    @patch.object(CommunicatorStrategy, '_get_config', fake_config)
    def test_get_slack_instance(self):
        slack = CommunicatorStrategy.get_instance()
        self.assertTrue(slack.__class__.__name__ == 'Slack')
