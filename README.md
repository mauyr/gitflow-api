# Gitflow
Gitflow é uma biblioteca para que possa utilizar a metodologia Gitflow usando o o Gitlab ou Github como API.

### Requirements
Gitflow necessita que tenha o executável do `git` e uma instalação do Gitlab ou Github com acesso de sua API via Token.

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

`http://pypi.python.org/pypi/gitflow-api`

If you like to clone from source, you can do it like so:

`git clone https://github.com/mauyr/gitflow-api.git`

### Binary distribution
`pyinstaller --onefile gitflow_api/gitflow.py`


### RUNNING TESTS
`python -m tests`


## Usability

### Hotfix
`gitflow hotfix-start --branch=hotfix-branch-1`

`gitflow hotfix-finish` 

### Features
`gitflow feature-start --branch=feature-branch-1`

`gitflow feature-finish`


### Release
`gitflow release-start`

`gitflow release-finish`

`gitflow launch`

`gitflow changelog` 
