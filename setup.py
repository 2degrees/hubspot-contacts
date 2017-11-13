##############################################################################
#
# Copyright (c) 2014, 2degrees Limited.
# All Rights Reserved.
#
# This file is part of hubspot-contacts
# <https://github.com/2degrees/hubspot-contacts>, which is subject to the
# provisions of the BSD at
# <http://dev.2degreesnetwork.com/p/2degrees-license.html>. A copy of the
# license should accompany this distribution. THIS SOFTWARE IS PROVIDED "AS IS"
# AND ANY AND ALL EXPRESS OR IMPLIED WARRANTIES ARE DISCLAIMED, INCLUDING, BUT
# NOT LIMITED TO, THE IMPLIED WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST
# INFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
#
##############################################################################

import os

from setuptools import find_packages
from setuptools import setup

_CURRENT_DIR_PATH = os.path.abspath(os.path.dirname(__file__))

_README_CONTENTS = open(os.path.join(_CURRENT_DIR_PATH, 'README.rst')).read()
_CHANGELOG_PATH = \
    os.path.join(_CURRENT_DIR_PATH, 'docs', 'source', 'changelog.rst')
_CHANGELOG_CONTENTS = open(_CHANGELOG_PATH).read()

_VERSION = \
    open(os.path.join(_CURRENT_DIR_PATH, 'VERSION.txt')).readline().rstrip()

_LONG_DESCRIPTION = _README_CONTENTS + '\n' + _CHANGELOG_CONTENTS


setup(
    name='hubspot-contacts',
    version=_VERSION,
    description='Pythonic wrapper for HubSpot API methods in the Contacts, '
        'Contact Lists and Contact Properties APIs',
    long_description=_LONG_DESCRIPTION,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python',
        ],
    keywords='hubspot contacts lists properties',
    author='2degrees Limited',
    author_email='2degrees-floss@googlegroups.com',
    url='http://pythonhosted.org/hubspot-contacts/',
    license='BSD (http://dev.2degreesnetwork.com/p/2degrees-license.html)',
    packages=find_packages(exclude=['tests']),
    namespace_packages=['hubspot'],
    install_requires=[
        'hubspot-connection >= 1.0rc2',
        'pyrecord >= 1.0a1',
        'voluptuous == 0.8.4',
        ],
    test_suite='nose.collector',
    )
