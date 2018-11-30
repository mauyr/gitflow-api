#!/usr/bin/env python
from __future__ import print_function
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

install_requires = ['GitPython>=2.1.11','python-gitlab>=1.6.0']
test_requires = []
# end

setup(
    name="GitLab-Gitflow",
    version="0.0.1",
    description="Gitlab with Gitflow library",
    author="Mauyr Alexandre Pereira",
    author_email="mauyr.pereira@inovapro.com.br",
    url="https://github.com/mauyr/gitlab-gitflow",
    packages=find_packages('.'),
    license="GNU GPLv3",
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    install_requires=install_requires,
    test_requirements=test_requires + install_requires,
    long_description="Gitlab with Gitflow is a python library used use a gitflow methodology on development "
                     "enviroment using a Gitlab-API with backend",
    classifiers=[
        # Picked from
        #   http://pypi.python.org/pypi?:action=list_classifiers
        # "Development Status :: 1 - Planning",
        "Development Status :: 2 - Pre-Alpha",
        # "Development Status :: 3 - Alpha",
        # "Development Status :: 4 - Beta",
        # "Development Status :: 5 - Production/Stable",
        # "Development Status :: 6 - Mature",
        # "Development Status :: 7 - Inactive",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ]
)