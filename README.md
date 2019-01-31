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

`pip install gitflow-api`

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
Hotfix são sempre criados a partir da branch master³ e devem ser utilizados para correções emergenciais.

##### Criando uma novo Hotfix 
`gitflow hotfix-start hotfix-branch-1`

Podem ser executado de qualquer branch, porém cuidado com arquivos não commitados para não ocasionar conflitos.

Fluxo de execuções:
* Checkout da branch master³
* Pull
* Cria nova branch com o nome do argumento passado mais o prefixo **hotfix/**
* Checkout para a nova branch
* Push da nova branch para origin
* Cria um novo merge request¹ classificado como bug² em estado WIP

##### Finalizando um Hotfix
`gitflow hotfix-finish`

Se executado diretamente na branch que deseja finalizar.

`gitflow hotfix-finish hotfix-branch-1`

Para executar a partir de outra branch.
 
Fluxo de execuções:
* Opcional: Checkout da branch passada
* Checa se merge request¹ não tem conflitos ou está em algum estado que impeça sua reintegração
* Em caso de conflito, tenta fazer merge automático
* Realiza o merge com a branch master³
* Push de todas as alterações

### Features
Features são sempre criados a partir da branch staging³ e devem ser utilizados para novas funcionalidades, débitos técnicos ou bugs não emergenciais.

##### Criando uma nova Feature
`gitflow feature-start feature-branch-1`

Podem ser executado de qualquer branch, porém cuidado com arquivos não commitados para não ocasionar conflitos.

Fluxo de execuções:
* Checkout da branch staging³
* Pull
* Cria nova branch com o nome do argumento passado mais prefixo **feature/**
* Checkout para a nova branch
* Push da nova branch para origin
* Cria um novo merge request¹ classificado como feature² em estado WIP

##### Finalizando uma Feature
`gitflow feature-finish`

Se executado diretamente na branch que deseja finalizar.

`gitflow feature-finish feature-branch-1`

Para executar a partir de outra branch.
 
Fluxo de execuções:
* Opcional: Checkout da branch passada
* Checa se merge request¹ não tem conflitos ou está em algum estado que impeça sua reintegração
* Em caso de conflito, tenta fazer merge automático
* Realiza o merge com a branch staging³
* Push de todas as alterações

### Release
`gitflow release-start`

`gitflow release-finish`

`gitflow launch`

`gitflow changelog` 
