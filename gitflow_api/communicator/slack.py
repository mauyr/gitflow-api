#!/usr/bin/env python
# encoding: utf-8
import json
import requests

from gitflow_api.communicator.communicator import Communicator


class Slack(Communicator):

    def __init__(self, release_webhook, launch_webhook):
        super(Slack, self).__init__(release_webhook, launch_webhook)

    def send_message(self, message, channel):
        json = SlackPostMessage(message, 'Gitflow-API').toJSON()
        r = requests.post(channel, json=json)
        return requests.post(channel, json=json)

    def send_changelog(self, changelog, channel):
        message = SlackPostMessage(self._make_changelog_slack_format(changelog), 'Gitflow-API').toJSON()
        return requests.post(channel, data=message)

    @staticmethod
    def _make_changelog_slack_format(changelog_issues):
        merge_request_md = ''
        if len(changelog_issues.stories) > 0:
            merge_request_md = merge_request_md + '\n' + str('*Improvements*')
            for issue in changelog_issues.stories:
                merge_request_md = merge_request_md + '\n' + str('- <{}|{}>').format(issue.url, issue.title)

        if len(changelog_issues.bugs) > 0:
            merge_request_md = merge_request_md + '\n' + str('*Bugs*')
            for issue in changelog_issues.bugs:
                merge_request_md = merge_request_md + '\n' + str('- <{}|{}>').format(issue.url, issue.title)

        if len(changelog_issues.technicalDebts) > 0:
            merge_request_md = merge_request_md + '\n' + str('*Technical Debts*')
            for issue in changelog_issues.technicalDebts:
                merge_request_md = merge_request_md + '\n' + str('- <{}|{}>').format(issue.url, issue.title)

        if len(changelog_issues.others) > 0:
            merge_request_md = merge_request_md + '\n' + str('*Others*')
            for issue in changelog_issues.others:
                merge_request_md = merge_request_md + '\n' + str('- <{}|{}>').format(issue.url, issue.title)

        return merge_request_md


class SlackPostMessage:
    text = ''
    username = ''
    mrkdwn = True

    def __init__(self, text, username):
        self.text = text
        self.username = username
        self.mrkdwn = True

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)