#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Based on https://github.com/kennethreitz/setup.py

import io
import os

from setuptools import setup

# Package meta-data.
NAME = 'alerta_opendxl'
DESCRIPTION = 'Broadcast incoming Alerta alerts to a OpenDXL event topic'
URL = 'https://github.com/ccdcoe/roboblue/tree/master/alerta_opendxl'
EMAIL = 'me@example.com'
AUTHOR = 'CCDCOE'
REQUIRES_PYTHON = '>=3.0.0'
VERSION = '0.0.1'

# What packages are required for this module to be executed?
REQUIRED = [
    "dxlclient>=5.0.0.568",
    "alerta-server",
    # DXL client dependency pulls in requests, but does not specify version. Will clash on older debian without
    # intervention
    "requests>=2.21.0"
]

# What packages are optional?
EXTRAS = {}

CLASSIFIERS = [
    # Trove classifiers
    # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    'Programming Language :: Python',
    'Programming Language :: Python :: 3'
]

# The rest you shouldn't have to touch too much :)
# ------------------------------------------------
# Except, perhaps the License and Trove Classifiers!
# If you do change the License, remember to change the Trove Classifier for that!

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
    with open(os.path.join(here, NAME, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION

# Where the magic happens:
setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    py_modules=['alerta_opendxl'],
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    entry_points={
        'alerta.plugins': [
            'opendxl = alerta_opendxl:OpenDxlPublisher'
        ]
    },
    license='MIT',
    classifiers=CLASSIFIERS,
)
