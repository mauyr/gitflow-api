#!/usr/bin/env python

from enum import Enum


class ApiStrategy:

    def get_instance(self, api):
        if Api.GITLAB == api:
            pass
        elif Api.GITHUB == api:
            pass
        else:
            raise NotImplementedError('Api not supported!')


class Api(Enum):
    GITLAB = 0
    GITHUB = 1
