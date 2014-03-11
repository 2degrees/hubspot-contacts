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

from json import dumps as json_serialize

from nose.tools import assert_dict_contains_subset
from nose.tools import assert_false
from nose.tools import assert_in
from nose.tools import assert_is_instance
from nose.tools import assert_raises
from nose.tools import eq_
from nose.tools import ok_
from requests.adapters import HTTPAdapter as RequestsHTTPAdapter
from requests.models import Response as RequestsResponse
from six.moves.urllib.parse import parse_qs
from six.moves.urllib.parse import urlparse

from hubspot.contacts.connection import APIKey
from hubspot.contacts.connection import OAuthKey
from hubspot.contacts.connection import PortalConnection
from hubspot.contacts.exc import HubspotAuthenticationError
from hubspot.contacts.exc import HubspotClientError
from hubspot.contacts.exc import HubspotServerError
from hubspot.contacts.exc import HubspotUnsupportedResponseError

from tests.utils.generic import get_uuid4_str


_STUB_PATH_INFO = '/foo'

_STUB_AUTHENTICATION_KEY = APIKey(get_uuid4_str())


class TestPortalConnection(object):

    def test_get_request(self):
        self._check_request_sender('GET', 'send_get_request', False)

    def test_post_request(self):
        self._check_request_sender('POST', 'send_post_request', True)

    def test_put_request(self):
        self._check_request_sender('PUT', 'send_put_request', True)

    def test_delete_request(self):
        self._check_request_sender('DELETE', 'send_delete_request', False)

    @staticmethod
    def _check_request_sender(
        http_method_name,
        request_sender_name,
        include_request_body,
        ):
        connection = _MockPortalConnection()

        body_deserialization = {'foo': 'bar'} if include_request_body else None

        request_sender = getattr(connection, request_sender_name)
        request_sender_kwargs = {}
        if include_request_body:
            request_sender_kwargs['body_deserialization'] = body_deserialization
        request_sender(_STUB_PATH_INFO, **request_sender_kwargs)

        eq_(1, len(connection.prepared_requests))

        prepared_request = connection.prepared_requests[0]
        eq_(http_method_name, prepared_request.method)

        requested_path_info = \
            _get_path_info_from_contacts_api_url(prepared_request.url)
        eq_(_STUB_PATH_INFO, requested_path_info)

        if include_request_body:
            body_serialization = json_serialize(body_deserialization)
            eq_(body_serialization, prepared_request.body)
        else:
            assert_false(prepared_request.body)

    def test_user_agent(self):
        connection = _MockPortalConnection()

        connection.send_get_request(_STUB_PATH_INFO)

        prepared_request = connection.prepared_requests[0]
        assert_in('User-Agent', prepared_request.headers)

        user_agent_header_value = prepared_request.headers['User-Agent']
        ok_(user_agent_header_value.startswith('hubspot-contacts/'))

    def test_change_source(self):
        change_source = get_uuid4_str()
        connection = _MockPortalConnection(change_source=change_source)

        connection.send_get_request(_STUB_PATH_INFO)

        prepared_request = connection.prepared_requests[0]
        query_string_args = \
            _get_query_string_args_from_url(prepared_request.url)
        expected_change_source_args = {'auditId': [change_source]}
        assert_dict_contains_subset(
            expected_change_source_args,
            query_string_args,
            )

    def test_with_extra_query_string_args(self):
        """
        Any extra query string argument co-exists with authentication-related
        arguments.
        
        """
        connection = _MockPortalConnection()

        extra_query_string_args = {'foo': ['bar']}
        connection.send_get_request(_STUB_PATH_INFO, extra_query_string_args)

        prepared_request = connection.prepared_requests[0]
        query_string_args = \
            _get_query_string_args_from_url(prepared_request.url)
        assert_dict_contains_subset(extra_query_string_args, query_string_args)

    def test_json_response(self):
        """
        The output of "200 OK" responses with a JSON body is that body
        deserialized.

        """
        expected_body_deserialization = {'foo': 'bar'}
        response_maker = _ResponseMaker(200, expected_body_deserialization)
        connection = _MockPortalConnection(response_maker)

        response_data = connection.send_get_request(_STUB_PATH_INFO)

        eq_(expected_body_deserialization, response_data)

    def test_no_content_response(self):
        """There's no output for "204 NO CONTENT" responses."""
        connection = _MockPortalConnection()

        response_data = connection.send_get_request(_STUB_PATH_INFO)

        eq_(None, response_data)

    def test_unexpected_response_status_code(self):
        """
        An exception is raised when the response status code is unsupported.

        """
        unsupported_response_maker = _ResponseMaker(304, None)
        connection = _MockPortalConnection(unsupported_response_maker)

        with assert_raises(HubspotUnsupportedResponseError) as context_manager:
            connection.send_get_request(_STUB_PATH_INFO)

        exception = context_manager.exception
        eq_('Unsupported response status 304', str(exception))

    def test_unexpected_response_content_type(self):
        """
        An exception is raised when the response status code is 200 but the
        content type is not "application/json".

        """
        unsupported_response_maker = _ResponseMaker(200, 'Text', 'text/plain')
        connection = _MockPortalConnection(unsupported_response_maker)

        with assert_raises(HubspotUnsupportedResponseError) as context_manager:
            connection.send_get_request(_STUB_PATH_INFO)

        exception = context_manager.exception
        eq_('Unsupported response content type text/plain', str(exception))

    def test_missing_response_content_type(self):
        """An exception is raised when the content type is missing."""
        unsupported_response_maker = _ResponseMaker(200, 'Text', None)
        connection = _MockPortalConnection(unsupported_response_maker)

        with assert_raises(HubspotUnsupportedResponseError) as context_manager:
            connection.send_get_request(_STUB_PATH_INFO)

        exception = context_manager.exception
        eq_('Response does not specify a Content-Type', str(exception))

    def test_context_manager(self):
        with _MockPortalConnection() as connection:
            assert_is_instance(connection, _MockPortalConnection)

        assert_false(connection.adapter.is_open)

    def test_keep_alive(self):
        connection = _MockPortalConnection()
        connection.send_get_request(_STUB_PATH_INFO)
        ok_(connection.adapter.is_keep_alive_always_used)


class TestErrorResponses(object):

    def test_server_error_response(self):
        response_maker = _ResponseMaker(500, None)
        connection = _MockPortalConnection(response_maker)
        with assert_raises(HubspotServerError) as context_manager:
            connection.send_get_request(_STUB_PATH_INFO)

        exception = context_manager.exception
        assert_in('500', str(exception))

    def test_client_error_response(self):
        request_id = get_uuid4_str()
        error_message = 'Json node is missing child property'
        body_deserialization = {
            'status': 'error',
            'message': error_message,
            'requestId': request_id,
            }
        response_maker = _ResponseMaker(400, body_deserialization)
        connection = _MockPortalConnection(response_maker)

        with assert_raises(HubspotClientError) as context_manager:
            connection.send_get_request(_STUB_PATH_INFO)

        exception = context_manager.exception
        eq_(request_id, exception.request_id)
        eq_(error_message, str(exception))


class TestAuthentication(object):

    def test_oauth_token(self):
        self._assert_credentials_set_in_request(OAuthKey, 'access_token')

    def test_api_key(self):
        self._assert_credentials_set_in_request(APIKey, 'hapikey')

    @staticmethod
    def _assert_credentials_set_in_request(key_class, expected_key_name):
        authentication_key_value = get_uuid4_str()
        authentication_key = key_class(authentication_key_value)
        connection = \
            _MockPortalConnection(authentication_key=authentication_key)

        connection.send_get_request(_STUB_PATH_INFO)

        expected_credentials = {expected_key_name: [authentication_key_value]}
        prepared_request = connection.prepared_requests[0]
        query_string_args = \
            _get_query_string_args_from_url(prepared_request.url)
        assert_dict_contains_subset(expected_credentials, query_string_args)

    def test_unauthorized_response(self):
        request_id = get_uuid4_str()
        error_message = 'Invalid credentials'
        response_maker = _ResponseMaker(
            401,
            {
                'status': 'error',
                'message': error_message,
                'requestId': request_id,
                },
            )
        connection = _MockPortalConnection(
            response_maker,
            authentication_key=_STUB_AUTHENTICATION_KEY,
            )

        with assert_raises(HubspotAuthenticationError) as context_manager:
            connection.send_get_request(_STUB_PATH_INFO)

        exception = context_manager.exception

        eq_(request_id, exception.request_id)
        eq_(error_message, str(exception))


class _MockPortalConnection(PortalConnection):

    def __init__(
        self,
        response_maker=None,
        authentication_key=_STUB_AUTHENTICATION_KEY,
        change_source=None,
        *args,
        **kwargs
        ):
        super_class = super(_MockPortalConnection, self)
        super_class.__init__(authentication_key, change_source, *args, **kwargs)

        self.adapter = _MockRequestsAdapter(response_maker)
        self._session.mount(self._API_URL, self.adapter)

    @property
    def prepared_requests(self):
        return self.adapter.prepared_requests


class _MockRequestsAdapter(RequestsHTTPAdapter):

    def __init__(self, response_maker=None, *args, **kwargs):
        super(_MockRequestsAdapter, self).__init__(*args, **kwargs)

        self._response_maker = response_maker or _EMPTY_RESPONSE_MAKER

        self.prepared_requests = []
        self.is_keep_alive_always_used = True
        self.is_open = True

    def send(self, request, stream=False, *args, **kwargs):
        is_keep_alive_implied = not stream
        self.is_keep_alive_always_used &= is_keep_alive_implied

        self.prepared_requests.append(request)

        response = self._response_maker(request)
        return response

    def close(self, *args, **kwargs):
        self.is_open = False

        return super(_MockRequestsAdapter, self).close(*args, **kwargs)


class _ResponseMaker(object):

    def __init__(
        self,
        status_code,
        body_deserialization,
        content_type='application/json',
        ):
        super(_ResponseMaker, self).__init__()

        self._status_code = status_code
        self._body_deserialization = body_deserialization
        self._content_type = content_type

    def __call__(self, request):
        response = RequestsResponse()

        response.status_code = self._status_code

        if self._content_type:
            content_type_header_value = \
                '{}; charset=UTF-8'.format(self._content_type)
            response.headers['Content-Type'] = content_type_header_value

        if self._status_code != 204:
            response._content = json_serialize(self._body_deserialization)

        return response


_EMPTY_RESPONSE_MAKER = _ResponseMaker(204, None)


def _get_path_info_from_contacts_api_url(contacts_api_url):
    assert contacts_api_url.startswith(PortalConnection._API_URL)

    contacts_api_url_length = len(PortalConnection._API_URL)
    path_and_query_string = contacts_api_url[contacts_api_url_length:]
    path_info = path_and_query_string.split('?')[0]
    return path_info


def _get_query_string_args_from_url(url):
    url_parts = urlparse(url)
    query_string_raw = url_parts.query
    if query_string_raw:
        query_string_args = parse_qs(query_string_raw, strict_parsing=True)
    else:
        query_string_args = {}
    return query_string_args
