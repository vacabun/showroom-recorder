#!/usr/bin/env python3
import os
import json
import importlib
import setuptools

PROJ_NAME = 'showroom-recorder'
PACKAGE_NAME = 'showroom_recorder'

PROJ_METADATA = '%s.json' % PROJ_NAME

here = os.path.abspath(os.path.dirname(__file__))
proj_info = json.loads(open(os.path.join(here, PROJ_METADATA), encoding='utf-8').read())

Description = open(os.path.join(here, 'description.md'), encoding='utf-8').read()

VERSION = importlib.machinery.SourceFileLoader("version", os.path.join(here, 'src/%s/version.py' % PACKAGE_NAME)).load_module().__version__

setuptools.setup(
    name=proj_info['name'],
    version=VERSION,
    author=proj_info['author'],
    url=proj_info['url'],
    author_email=proj_info['author_email'],
    description=proj_info['description'],
    keywords=proj_info['keywords'],
    long_description=Description,
    long_description_content_type='text/markdown',
    packages=setuptools.find_packages('src'),
    package_dir={'': 'src'},
    test_suite='tests',
    platforms='any',
    zip_safe=True,
    include_package_data=True,
    entry_points={'console_scripts': proj_info['console_scripts']},
    install_requires=proj_info['install_requires']
)
