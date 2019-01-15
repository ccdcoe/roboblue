#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Based on https://github.com/kennethreitz/setup.py

import io
import os

from setuptools import setup

# Package meta-data.
NAME = 'dxlhistorian'
DESCRIPTION = 'DXLHistorian is a passive DXL event channel listener recording incoming events'
URL = 'https://github.com/ccdcoe/roboblue/tree/master/dxlhistorian'
EMAIL = 'me@example.com'
AUTHOR = 'CCDCOE'
REQUIRES_PYTHON = '>=2.7.9,<3.0'
VERSION = None

# What packages are required for this module to be executed?
REQUIRED = [
    "dxlclient>=5.0.0.568"
    "cffi>=1.11.5",
    "configobj>=5.0.6",
    "elasticsearch<7.0.0,>=6.0.0"
]

# What packages are optional?
EXTRAS = {}

CLASSIFIERS = [
    # Trove classifiers
    # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 2.7',
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
        exec (f.read(), about)
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
    packages=['dxlhistorian'],
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='MIT',
    classifiers=CLASSIFIERS,
)
