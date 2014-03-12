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

from nose.tools import eq_
from pyrecord import Record

from tests.utils.generic import convert_object_strings_to_unicode


MockRequestData = Record.create_type(
    'MockRequestData',
    'method',
    'path_info',
    'query_string_args',
    'body_deserialization',
    query_string_args=None,
    body_deserialization=None,
    )


class MockPortalConnection(object):

    def __init__(self, response_data_maker=None):
        super(MockPortalConnection, self).__init__()

        self._response_data_maker = response_data_maker
        self.requests_data = []

    def send_get_request(self, path_info, query_string_args=None):
        query_string_args = query_string_args or {}
        request_data = MockRequestData(
            'GET',
            path_info,
            query_string_args,
            )
        return self._send_request(request_data)

    def send_post_request(self, path_info, body_deserialization):
        request_data = MockRequestData(
            'POST',
            path_info,
            body_deserialization=body_deserialization,
            )
        return self._send_request(request_data)

    def send_put_request(self, path_info, body_deserialization):
        request_data = MockRequestData(
            'PUT',
            path_info,
            body_deserialization=body_deserialization,
            )
        return self._send_request(request_data)

    def _send_request(self, request_data):
        self.requests_data.append(request_data)

        if self._response_data_maker:
            response_data = self._response_data_maker(request_data)
        else:
            response_data = None
        return convert_object_strings_to_unicode(response_data)

    def assert_requested_path_infos_equal(self, expected_path_info):
        for request_data in self.requests_data:
            eq_(expected_path_info, request_data.path_info)

    def assert_request_methods_equal(self, expected_request_method):
        for request_data in self.requests_data:
            eq_(expected_request_method, request_data.method)
