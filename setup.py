#!/usr/bin/env python
from setuptools import setup, find_packages

install_requires = ['GitPython>=2.1.11','python-gitlab>=1.6.0','slackclient>=1.3.0']
test_requires = []
# end

setup(
    name="gitflow-api",
    version="0.3.8",
    description="Gitflow-API library using a API as backend",
    author="Mauyr Alexandre Pereira",
    author_email="mauyr.pereira@inovapro.com.br",
    url="https://github.com/mauyr/gitflow-api",
    packages=find_packages('.'),
    entry_points = {
        'console_scripts': ['gitflow=gitflow_api.gitflow:main'],
    },
    license="GNU GPLv3",
    python_requires='>=3.0',
    install_requires=install_requires,
    long_description="Gitflow-API is a python library used use a gitflow_methodology on development using a API like "
                     "Gitlab or Github to execute most of process",
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7"
    ]
)