# Gitlab-Gitflow
Gitlab-Gitflow é uma biblioteca para que possa utilizar a metodologia Gitflow usando o o Gitlab como API.

### Requirements
Gitlab-Gitflow necessita que tenha o executável do `git` e uma instalação do Gitlab com acesso via de sua API via Token.

* Git (1.7.x or newer)
* Python 2.7 to 3.7.
* Gitlab with v4 api

### Install
If you have downloaded the source code:

`python setup.py install`

or if you want to obtain a copy from the Pypi repository:

`pip install Gitlab-Gitflow`

Both commands will install the required package dependencies.

A distribution package can be obtained for manual installation at:

`http://pypi.python.org/pypi/Gitlab-Gitflow`

If you like to clone from source, you can do it like so:

`git clone https://github.com/mauyr/gitlab-gitflow.git`

### RUNNING TESTS
`python -m tests`


## Usability

### Hotfix
`gitflow.py hotfix-start --branch=hotfix-branch-1`

`gitflow.py hotfix-finish` 

### Features
`gitflow.py feature-start --branch=feature-branch-1`

`gitflow.py feature-finish`


### Release
`gitflow.py release-start`

`gitflow.py release-finish`

`gitflow.py launch`

`gitflow.py changelog`