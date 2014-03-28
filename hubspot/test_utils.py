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

from collections import namedtuple

from pyrecord import Record

from tests.utils.generic import convert_object_strings_to_unicode


# namedtuple is used instead of a record because we need immutable instances
RemoteMethod = namedtuple('RemoteMethod', ['path_info', 'http_method'])


RemoteMethodInvocation = Record.create_type(
    'RemoteMethodInvocation',
    'remote_method',
    'query_string_args',
    'body_deserialization',
    query_string_args=None,
    body_deserialization=None,
    )


class MockPortalConnection(object):

    def __init__(self, response_data_maker_by_remote_method=None):
        super(MockPortalConnection, self).__init__()

        self.response_data_maker_by_remote_method = \
            response_data_maker_by_remote_method or {}
        self.remote_method_invocations = []

    def send_get_request(self, path_info, query_string_args=None):
        remote_method = RemoteMethod(path_info, 'GET')
        return self._call_remote_method(remote_method, query_string_args)

    def send_post_request(self, path_info, body_deserialization):
        remote_method = RemoteMethod(path_info, 'POST')
        return self._call_remote_method(
            remote_method,
            body_deserialization=body_deserialization,
            )

    def send_put_request(self, path_info, body_deserialization):
        remote_method = RemoteMethod(path_info, 'PUT')
        return self._call_remote_method(
            remote_method,
            body_deserialization=body_deserialization,
            )

    def send_delete_request(self, path_info):
        remote_method = RemoteMethod(path_info, 'DELETE')
        return self._call_remote_method(remote_method)

    def _call_remote_method(
        self,
        remote_method,
        query_string_args=None,
        body_deserialization=None,
        ):
        remote_method_invocation = RemoteMethodInvocation(
            remote_method,
            query_string_args,
            body_deserialization,
            )
        self.remote_method_invocations.append(remote_method_invocation)

        if self.response_data_maker_by_remote_method:
            response_data_maker = \
                self.response_data_maker_by_remote_method[remote_method]
            response_data = \
                response_data_maker(query_string_args, body_deserialization)
        else:
            response_data = None
        return convert_object_strings_to_unicode(response_data)
