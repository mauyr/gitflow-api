#!/usr/bin/env python

import gitlab_manager
import os
from utilities.git_helper import GitHelper


class MergeRequest:

    def find_merge_request_by_url_and_branch(self, git_url, branch):
        project = self.find_project_by_url(git_url)

        return self.find_merge_request_by_project_and_branch(project, branch)

    def find_merge_request_by_project_and_branch(self, project, branch):
        if project.mergerequests is None:
            return None

        merge_requests = project.mergerequests.list(state='opened')

        filtered_merge_requests = list(filter(lambda x: str(x.source_branch) == str(branch), merge_requests))
        if len(filtered_merge_requests) == 0:
            return None
        else:
            return filtered_merge_requests[0]

    def _find_merge_request_by_url_and_branches(self, git_url, branch_from, branch_to):
        project = self.find_project_by_url(git_url)

        if project.mergerequests is None:
            return None

        merge_requests = project.mergerequests.list(state='opened')

        filtered_merge_requests = list(
            filter(lambda x: str(x.source_branch) == str(branch_from) and str(x.target_branch) == str(branch_to),
                   merge_requests))
        if len(filtered_merge_requests) == 0:
            return None
        else:
            return filtered_merge_requests[0]

    def find_merge_request_by_commit_message(self, commit_message):
        merge_request_code = commit_message[commit_message.find('See merge request ') + 18:]

        group_name = merge_request_code[:merge_request_code.find('/')]
        project_name = merge_request_code[merge_request_code.find('/') + 1:merge_request_code.find('!')]
        merge_request_id = merge_request_code[merge_request_code.find('!') + 1:].replace('\n', '')

        group = self.find_group_by_name(group_name)
        project = self._find_project_by_group_and_name(group, project_name)
        return project.mergerequests.get(merge_request_id)

    def _make_merge_request_description(self, model, description, issue_id):
        if description is not None:
            return description

        if model is not None:
            replaced_model = model
        else:
            replaced_model = 'Closes #0'

        if issue_id is not None:
            replaced_model.replace('Closes #0', 'Closes #' + str(issue_id))

        return replaced_model

    def _get_merge_request_md(self, path):
        merge_request_md_file = path + '/.gitlab_manager/merge_request_templates/merge_request.md'

        if os.path.exists(merge_request_md_file):
            F = open(merge_request_md_file, 'r')
            return F.read()
        else:
            return None

    def create_merge_request(self, git_url, branch_from, title, description, issue_id, to_branch, label):
        project = self.find_project_by_url(git_url)

        merge_request = self._find_merge_request_by_url_and_branches(git_url, branch_from, to_branch)

        if merge_request is None:
            merge_request_md = self._get_merge_request_md(self.path)

            description = self._make_merge_request_description(merge_request_md, description, issue_id)
            labels = []
            if label is not None:
                labels = [label]

            merge_request_model = {
                'source_branch': branch_from,
                'target_branch': to_branch,
                'title': (branch_from if title is None else title),
                'labels': labels,
                'description': description,
                'remove_source_branch': True
            }

            merge_request = project.mergerequests.create(merge_request_model)

        return merge_request

    def _validate_merge_request(self, merge_request):
        if merge_request is None:
            raise RuntimeWarning('Merge request not found for current branch')

        if bool(merge_request.work_in_progress):
            raise ValueError('Merge Request {} - {} on WIP status'.format(merge_request.iid, merge_request.title))

        if bool(merge_request.discussion_locked):
            raise ValueError(
                'Merge Request {} - {} has discussion unresolved'.format(merge_request.iid, merge_request.title))

        if str(merge_request.merge_status) != 'can_be_merged':
            raise ValueError(
                'Merge Request {} - {} is not ready for merge'.format(merge_request.iid, merge_request.title))

        return True

    def validate_merge_request_by_url_and_branch(self, git_url, branch):
        merge_request = self.find_merge_request_by_url_and_branch(git_url, branch)
        return self._validate_merge_request(merge_request)

    def validate_merge_request_by_url_and_branches(self, git_url, branch_from, branch_to):
        merge_request = self._find_merge_request_by_url_and_branches(git_url, branch_from, branch_to)

        return self._validate_merge_request(merge_request)

    def validate_and_close_merge_request(self, git_url, branch):
        mergeRequest = self.find_merge_request_by_url_and_branch(git_url, branch)

        if self._validate_merge_request(mergeRequest):
            mergeRequest.merge()

    def validate_and_close_merge_request_by_branches(self, git_url, branch_from, branch_to):
        merge_request = self._find_merge_request_by_url_and_branches(git_url, branch_from, branch_to)

        if self._validate_merge_request(merge_request):
            merge_request.merge()
