#!/usr/bin/env python
# coding: utf-8
# flake8: noqa

from setuptools import find_packages
from setuptools import setup

import codecs
import json
import os

project_root_dir = os.path.dirname(os.path.abspath(__file__))

def read(fname):
    file_path = os.path.join(project_root_dir, fname)
    with codecs.open(file_path, encoding='utf-8') as fd:
        content = fd.read()
    return content


def read_json(fname):
    jdata = json.loads(read(fname))
    return jdata

pkg_data = read_json('src/ipcrawl/metadata.json')

setup(
    name=pkg_data['package_name'],
    version=pkg_data['version'],
    author=pkg_data['author'],
    author_email=pkg_data['author_email'],
    maintainer=pkg_data['author'],
    maintainer_email=pkg_data['author_email'],
    license=pkg_data['license'],
    url=pkg_data['url'],
    description=pkg_data['description'],
    long_description=read('README.md'),
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    python_requires='>=3.6',
    zip_safe=False,
    install_requires=[
        'sly==0.3',
        'SQLAlchemy==1.3.5',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Home Automation',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: BSD :: FreeBSD',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',
        'License :: OSI Approved :: {} License'.format(pkg_data['license']),
    ],
)
