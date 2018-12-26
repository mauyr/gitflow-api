#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase
from unittest.mock import patch

from gitflow_api.communicator.communicator_strategy import CommunicatorStrategy
from gitflow_api.services.changelog import Changelog, Issue, ChangelogIssues


class TestCommunicator(TestCase):

    @staticmethod
    def fake_changelog():
        stories = [Issue('Story 1 - Fake screen for fake app', 'http://127.0.0.1', 'story'),
                   Issue('Story 2 - Fake feature with fake button', 'http://127.0.0.1', 'story')]
        bugs = [Issue('Bug 1 - Fake bug fixed', 'http://127.0.0.1', 'bug')]
        changelog = ChangelogIssues()
        changelog.stories = stories
        changelog.bugs = bugs
        return changelog

    def test_send_changelog(self):
        changelog = TestCommunicator.fake_changelog()

        slack = CommunicatorStrategy.get_instance()
        response = slack.send_changelog(changelog, slack.release_webhook)
        self.assertTrue(response.status_code == 200)

