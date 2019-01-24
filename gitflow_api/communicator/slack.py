#!/usr/bin/env python
# encoding: utf-8
import json
import requests

from gitflow_api.communicator.communicator import Communicator


class Slack(Communicator):

    def __init__(self, release_webhook, launch_webhook):
        super(Slack, self).__init__(release_webhook, launch_webhook)

    def send_message(self, message, channel, project_name):
        json = SlackPostMessage(message, 'Gitflow-API').toJSON()
        r = requests.post(channel, json=json)
        return requests.post(channel, json=json)

    def send_changelog(self, changelog, channel, project_name):
        message = SlackPostMessage(self._make_changelog_slack_format(changelog, project_name), 'Gitflow-API').toJSON()
        return requests.post(channel, data=message)

    @staticmethod
    def _make_changelog_slack_format(changelog_issues, project_name):
        slack_format_changelog = []
        slack_format_changelog.append('*{} - {}*'.format(project_name, changelog_issues.version))
        if len(changelog_issues.stories) > 0:
            slack_format_changelog.append(str('*Improvements*'))
            for issue in changelog_issues.stories:
                slack_format_changelog.append(str('- <{}|{}>').format(issue.url, issue.title))

        if len(changelog_issues.bugs) > 0:
            slack_format_changelog.append(str('*Bugs*'))
            for issue in changelog_issues.bugs:
                slack_format_changelog.append(str('- <{}|{}>').format(issue.url, issue.title))

        if len(changelog_issues.technicalDebts) > 0:
            slack_format_changelog.append(str('*Technical Debts*'))
            for issue in changelog_issues.technicalDebts:
                slack_format_changelog.append(str('- <{}|{}>').format(issue.url, issue.title))

        if len(changelog_issues.others) > 0:
            slack_format_changelog.append(str('*Others*'))
            for issue in changelog_issues.others:
                slack_format_changelog.append(str('- <{}|{}>').format(issue.url, issue.title))

        return '\n'.join(slack_format_changelog)


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