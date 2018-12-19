#!/usr/bin/env python

# Config file
CONFIG_FILE = 'gitflow.config'

# Branches structure
MASTER_BRANCH = 'master'
STAGING_BRANCH = 'staging'

HOTFIX_BRANCH = 'hotfix/{}'
FEATURE_BRANCH = 'feature/{}'
RELEASE_BRANCH = 'release/{}'

VERSION = '{}-{}'

# Issue Classification - Api Labels
FEATURE_LABELS = ['story', 'feature']
CHANGE_LABELS = ['change']
BUG_LABELS = ['bug']
TECHNICAL_DEBT_LABELS = ['technical debt']
IGNORE_LABELS = ['ignore']
VERSION_LABEL_PREFIX = 'v.{}'
