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
from abc import abstractmethod

from nose.tools import eq_
from pyrecord import Record


MockRequestData = Record.create_type(
    'MockRequestData',
    'path_info',
    'query_string_args',
    )


class MockPortalConnection(object):

    __metaclass__ = ABCMeta

    def __init__(self):
        super(MockPortalConnection, self).__init__()

        self.requests_data = []

    def send_get_request(self, path_info, query_string_args=None):
        query_string_args = query_string_args or {}
        request_data = MockRequestData(path_info, query_string_args)

        self.requests_data.append(request_data)

        stub_data = self._get_stub_data(request_data)
        return stub_data

    @abstractmethod
    def _get_stub_data(self, request_data):
        pass

    def assert_requested_path_infos_equal(self, expected_path_info):
        for request_data in self.requests_data:
            eq_(expected_path_info, request_data.path_info)
