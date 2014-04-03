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

from abc import ABCMeta
from abc import abstractproperty

from nose.tools import eq_


class BaseMethodTestCase(object):

    __metaclass__ = ABCMeta

    _REMOTE_METHOD = abstractproperty()

    @classmethod
    def _assert_expected_remote_method_used(cls, connection):
        for remote_method_invocation in connection.remote_method_invocations:
            eq_(cls._REMOTE_METHOD, remote_method_invocation.remote_method)


class ConstantResponseDataMaker(object):

    def __init__(self, response_data):
        super(ConstantResponseDataMaker, self).__init__()
        self.response_data = response_data

    def __call__(self, query_string_args, body_deserialization):
        return self.response_data
