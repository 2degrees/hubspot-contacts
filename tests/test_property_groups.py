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

from nose.tools import assert_in
from nose.tools import assert_not_in
from nose.tools import assert_raises
from nose.tools import eq_

from hubspot.contacts.exc import HubspotClientError
from hubspot.contacts.properties import DatetimeProperty
from hubspot.contacts.properties import StringProperty
from hubspot.contacts.property_groups import PropertyGroup
from hubspot.contacts.property_groups import create_property_group
from hubspot.contacts.property_groups import get_all_property_groups

from tests.utils import BaseMethodTestCase
from tests.utils import RemoteMethod
from tests.utils.connection import MockPortalConnection
from tests.utils.generic import get_uuid4_str


class TestPropertyGroupCreation(BaseMethodTestCase):

    _PROPERTY_GROUP_NAME = 'test-property-group'

    _REMOTE_METHOD = RemoteMethod('/groups/' + _PROPERTY_GROUP_NAME, 'PUT')

    def test_display_name_specified(self):
        property_group = \
            PropertyGroup(self._PROPERTY_GROUP_NAME, 'Test Property Group')

        request_data, response_data = \
            self._create_property_group(property_group)

        eq_(property_group.name, request_data.body_deserialization['name'])
        eq_(
            property_group.display_name,
            request_data.body_deserialization['displayName'],
            )

        eq_(property_group.name, response_data['name'])
        eq_(property_group.display_name, response_data['displayName'])

    def test_display_name_not_specified(self):
        property_group = PropertyGroup(self._PROPERTY_GROUP_NAME)

        request_data, response_data = \
            self._create_property_group(property_group)

        assert_not_in('displayName', request_data.body_deserialization)

        eq_('', response_data['displayName'])

    def test_group_already_exists(self):
        connection = MockPortalConnection(
            _replicate_create_property_group_error_response,
            )

        property_group = PropertyGroup(self._PROPERTY_GROUP_NAME)

        with assert_raises(HubspotClientError) as context_manager:
            create_property_group(property_group, connection)

        exception = context_manager.exception
        assert_in(property_group.name, str(exception))

    def _create_property_group(self, property_group):
        connection = \
            MockPortalConnection(_replicate_create_property_group_response_data)

        response_data = create_property_group(property_group, connection)

        self._assert_expected_remote_method_used(connection)

        eq_(1, len(connection.requests_data))
        request_data = connection.requests_data[0]

        return request_data, response_data


def _replicate_create_property_group_response_data(request_data):
    response_data = {
        'name': request_data.body_deserialization['name'],
        'displayName': request_data.body_deserialization.get('displayName', ''),
        'displayOrder': 1,
        'portalId': 1,
        }
    return response_data


def _replicate_create_property_group_error_response(request_data):
    property_group_name = request_data.body_deserialization['name']
    raise HubspotClientError(
        "The Group named '{}' already exists.".format(property_group_name),
        get_uuid4_str(),
        )


class TestGettingAllPropertyGroups(BaseMethodTestCase):

    _REMOTE_METHOD = RemoteMethod('/groups', 'GET')

    _PROPERTY_GROUP_DATA = [
        {
            'name': 'groupa',
            'displayName': 'Group A',
            'properties': [
                {
                    'name': 'lastmodifieddate',
                    'type': 'datetime',
                    'label': '',
                    'description': '',
                    'fieldType': '',
                    'options': [],
                    'groupName': 'groupa',
                    },
                ],
            },
        {
            'name': 'groupb',
            'displayName': 'Group B',
            'properties': [
                {
                    'name': 'twitterhandle',
                    'type': 'string',
                    'label': '',
                    'description': '',
                    'fieldType': '',
                    'options': [],
                    'groupName': 'groupb',
                    },
                ],
            },
        ]

    def test_no_property_groups(self):
        connection = MockPortalConnection(lambda r: [])

        retrieved_property_groups = get_all_property_groups(connection)
        eq_(0, len(retrieved_property_groups))

        self._assert_expected_remote_method_used(connection)

    def test_property_groups_without_properties(self):
        property_group_data = self._PROPERTY_GROUP_DATA[0].copy()
        del property_group_data['properties']
        connection = MockPortalConnection(lambda r: [property_group_data])

        retrieved_property_groups = get_all_property_groups(connection)

        expected_property_groups = [PropertyGroup('groupa', 'Group A')]
        eq_(expected_property_groups, retrieved_property_groups)

        self._assert_expected_remote_method_used(connection)

    def test_multiple_property_groups(self):
        connection = MockPortalConnection(lambda r: self._PROPERTY_GROUP_DATA)

        retrieved_property_groups = get_all_property_groups(connection)

        expected_property_groups = [
            PropertyGroup(
                'groupa',
                'Group A',
                [DatetimeProperty('lastmodifieddate', '', '', 'groupa', '')],
                ),
            PropertyGroup(
                'groupb',
                'Group B',
                [StringProperty('twitterhandle', '', '', 'groupb', '' )],
                ),
            ]
        eq_(expected_property_groups, retrieved_property_groups)

        self._assert_expected_remote_method_used(connection)
