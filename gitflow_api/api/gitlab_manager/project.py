#!/usr/bin/env python
# encoding: utf-8

from gitflow_api.utilities.git_helper import GitHelper


class Project:
    global gl

    def __init__(self, gl):
        self.gl = gl

    def find_project_by_url(self, url):
        group_name, project_name = GitHelper.extract_group_and_project_from_url(url)
        group = self.find_group_by_name(group_name)

        return self.find_project_by_group_and_name(group, project_name)

    def find_group_by_name(self, group_name):
        group_name = self._get_last_group_name(group_name)
        groups = self.gl.groups.list(all=True)

        filtered_group = list(filter(lambda x: str(x.path).lower() == group_name.lower(), groups))
        if len(filtered_group) == 0:
            raise Exception('Group not found: {}'.format(group_name))
        else:
            return filtered_group[0]

    def find_project_by_group_and_name(self, group, project_name):
        projects = group.projects.list(all=True)
        project = list(filter(lambda x: x.name == project_name, projects))[0]
        return self.gl.projects.get(project.id)

    def _get_last_group_name(self, group_name):
        groups = group_name.split('/')
        return str(groups[len(groups)-1])