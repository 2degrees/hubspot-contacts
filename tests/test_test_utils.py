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

from nose.tools import assert_is_instance
from nose.tools import eq_

from hubspot.test_utils import MockPortalConnection
from hubspot.test_utils import RemoteMethod
from hubspot.test_utils import RemoteMethodInvocation

from tests.utils import ConstantResponseDataMaker


_STUB_PATH_INFO = '/foo'

_STUB_RESPONSE_DATA = {'foo': 'bar'}

_STUB_RESPONSE_DATA_MAKER = ConstantResponseDataMaker(_STUB_RESPONSE_DATA)


class TestMockPortalConnection(object):

    def test_get_request(self):
        remote_method = RemoteMethod(_STUB_PATH_INFO, 'GET')
        connection = self._make_connection_for_remote_method(remote_method)

        response_data = connection.send_get_request(_STUB_PATH_INFO)

        expected_remote_method_invocation = \
            RemoteMethodInvocation(remote_method)
        self._assert_sole_remote_method_invocation_equals(
            expected_remote_method_invocation,
            connection,
            )

        eq_(_STUB_RESPONSE_DATA, response_data)

    def test_get_request_with_query_string_args(self):
        remote_method = RemoteMethod(_STUB_PATH_INFO, 'GET')
        connection = self._make_connection_for_remote_method(remote_method)

        query_string_args = {'foo': 'bar'}
        response_data = \
            connection.send_get_request(_STUB_PATH_INFO, query_string_args)

        expected_remote_method_invocation = \
            RemoteMethodInvocation(remote_method, query_string_args)
        self._assert_sole_remote_method_invocation_equals(
            expected_remote_method_invocation,
            connection,
            )

        eq_(_STUB_RESPONSE_DATA, response_data)

    def test_post_request(self):
        remote_method = RemoteMethod(_STUB_PATH_INFO, 'POST')
        connection = self._make_connection_for_remote_method(remote_method)

        body_deserialization = {'foo': 'bar'}
        response_data = \
            connection.send_post_request(_STUB_PATH_INFO, body_deserialization)

        expected_remote_method_invocation = RemoteMethodInvocation(
            remote_method,
            body_deserialization=body_deserialization,
            )
        self._assert_sole_remote_method_invocation_equals(
            expected_remote_method_invocation,
            connection,
            )

        eq_(_STUB_RESPONSE_DATA, response_data)

    def test_put_request(self):
        remote_method = RemoteMethod(_STUB_PATH_INFO, 'PUT')
        connection = self._make_connection_for_remote_method(remote_method)

        body_deserialization = {'foo': 'bar'}
        response_data = \
            connection.send_put_request(_STUB_PATH_INFO, body_deserialization)

        expected_remote_method_invocation = RemoteMethodInvocation(
            remote_method,
            body_deserialization=body_deserialization,
            )
        self._assert_sole_remote_method_invocation_equals(
            expected_remote_method_invocation,
            connection,
            )

        eq_(_STUB_RESPONSE_DATA, response_data)

    def test_delete_request(self):
        remote_method = RemoteMethod(_STUB_PATH_INFO, 'DELETE')
        connection = self._make_connection_for_remote_method(remote_method)

        response_data = connection.send_delete_request(_STUB_PATH_INFO)

        expected_remote_method_invocation = \
            RemoteMethodInvocation(remote_method)
        self._assert_sole_remote_method_invocation_equals(
            expected_remote_method_invocation,
            connection,
            )

        eq_(_STUB_RESPONSE_DATA, response_data)

    def test_no_response_data_maker(self):
        connection = MockPortalConnection()

        response_data = connection.send_get_request(_STUB_PATH_INFO)

        eq_(None, response_data)

    def test_response_data_strings(self):
        """Strings in the response data are converted to unicode"""
        remote_method = RemoteMethod(_STUB_PATH_INFO, 'GET')
        connection = self._make_connection_for_remote_method(remote_method)

        response_data = connection.send_get_request(_STUB_PATH_INFO)
        string_values = response_data.keys() + response_data.values()
        for string_value in string_values:
            assert_is_instance(string_value, unicode)

    def _make_connection_for_remote_method(self, remote_method):
        response_data_maker_by_remote_method = \
            {remote_method: _STUB_RESPONSE_DATA_MAKER}
        connection = MockPortalConnection(response_data_maker_by_remote_method)
        return connection

    def _assert_sole_remote_method_invocation_equals(
        self,
        expected_remote_method_invocation,
        connection,
        ):
        eq_(
            [expected_remote_method_invocation],
            connection.remote_method_invocations,
            )
