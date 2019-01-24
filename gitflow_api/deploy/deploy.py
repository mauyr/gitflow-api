#!/usr/bin/env python
# encoding: utf-8
import abc


class Deploy(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, classtype):
        self._type = classtype

    @abc.abstractmethod
    def deploy(self):
        pass