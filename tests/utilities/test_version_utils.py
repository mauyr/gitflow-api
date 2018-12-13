#!/usr/bin/env python
# encoding: utf-8

from unittest import TestCase

from gitflow_api.utilities.version_utils import VersionUtils, Version


class TestVersionUtils(TestCase):
    def test_get_new_version_patch(self):
        new_version = VersionUtils.get_new_version('1.0.0', Version.PATCH, False, 1)
        self.assertEqual(new_version, '1.0.1')

    def test_get_new_version_minor(self):
        new_version = VersionUtils.get_new_version('1.0.0', Version.MINOR, False, 1)
        self.assertEqual(new_version, '1.1.0')

    def test_get_new_version_major(self):
        new_version = VersionUtils.get_new_version('1.0.0', Version.MAJOR, False, 1)
        self.assertEqual(new_version, '2.0.0')

    def test_get_new_version_patch_snapshot(self):
        new_version = VersionUtils.get_new_version('1.0.0', Version.PATCH, True, 1)
        self.assertEqual(new_version, '1.0.1-SNAPSHOT')

    def test_get_new_version_patch_decrement_invalid(self):
        new_version = VersionUtils.get_new_version('1.0.0', Version.PATCH, False, -1)
        self.assertEqual(new_version, '1.0.0')

    def test_get_new_version_patch_decrement_valid(self):
        new_version = VersionUtils.get_new_version('1.0.2', Version.PATCH, False, -1)
        self.assertEqual(new_version, '1.0.1')
