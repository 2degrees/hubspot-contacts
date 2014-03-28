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
from hubspot.test_utils import MockPortalConnection
from hubspot.test_utils import RemoteMethod

from tests.utils import BaseMethodTestCase
from tests.utils import ConstantResponseDataMaker
from tests.utils.generic import get_uuid4_str


class TestPropertyGroupCreation(BaseMethodTestCase):

    _PROPERTY_GROUP_NAME = 'test-property-group'

    _REMOTE_METHOD = RemoteMethod('/groups/' + _PROPERTY_GROUP_NAME, 'PUT')

    def test_display_name_specified(self):
        property_group = \
            PropertyGroup(self._PROPERTY_GROUP_NAME, 'Test Property Group')

        remote_method_invocation, created_property_group = \
            self._create_property_group(property_group)

        eq_(
            property_group.name,
            remote_method_invocation.body_deserialization['name'],
            )
        eq_(
            property_group.display_name,
            remote_method_invocation.body_deserialization['displayName'],
            )

        eq_(property_group, created_property_group)

    def test_display_name_not_specified(self):
        property_group = PropertyGroup(self._PROPERTY_GROUP_NAME)

        remote_method_invocation, created_property_group = \
            self._create_property_group(property_group)

        assert_not_in(
            'displayName',
            remote_method_invocation.body_deserialization,
            )

        eq_('', created_property_group.display_name)

    def test_group_already_exists(self):
        response_data_maker_by_remote_method = {
            self._REMOTE_METHOD:
                _replicate_create_property_group_error_response,
            }
        connection = MockPortalConnection(response_data_maker_by_remote_method)

        property_group = PropertyGroup(self._PROPERTY_GROUP_NAME)

        with assert_raises(HubspotClientError) as context_manager:
            create_property_group(property_group, connection)

        exception = context_manager.exception
        assert_in(property_group.name, str(exception))

    def _create_property_group(self, property_group):
        response_data_maker_by_remote_method = {
            self._REMOTE_METHOD: _replicate_create_property_group_response_data,
            }
        connection = MockPortalConnection(response_data_maker_by_remote_method)

        created_property_group = \
            create_property_group(property_group, connection)

        self._assert_expected_remote_method_used(connection)

        eq_(1, len(connection.remote_method_invocations))
        remote_method_invocation = connection.remote_method_invocations[0]

        return remote_method_invocation, created_property_group


def _replicate_create_property_group_response_data(
    remote_method,
    body_deserialization,
    ):
    response_data = {
        'name': body_deserialization['name'],
        'displayName': body_deserialization.get('displayName', ''),
        'displayOrder': 1,
        'portalId': 1,
        }
    return response_data


def _replicate_create_property_group_error_response(
    remote_method,
    body_deserialization,
    ):
    property_group_name = body_deserialization['name']
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
        response_data_maker_by_remote_method = \
            {self._REMOTE_METHOD: ConstantResponseDataMaker([])}
        connection = MockPortalConnection(response_data_maker_by_remote_method)

        retrieved_property_groups = get_all_property_groups(connection)
        eq_(0, len(retrieved_property_groups))

        self._assert_expected_remote_method_used(connection)

    def test_property_groups_without_properties(self):
        property_group_data = self._PROPERTY_GROUP_DATA[0].copy()
        del property_group_data['properties']

        response_data_maker = ConstantResponseDataMaker([property_group_data])
        response_data_maker_by_remote_method = \
            {self._REMOTE_METHOD: response_data_maker}
        connection = MockPortalConnection(response_data_maker_by_remote_method)

        retrieved_property_groups = get_all_property_groups(connection)

        expected_property_groups = [PropertyGroup('groupa', 'Group A')]
        eq_(expected_property_groups, retrieved_property_groups)

        self._assert_expected_remote_method_used(connection)

    def test_multiple_property_groups(self):
        response_data_maker_by_remote_method = \
            {self._REMOTE_METHOD: self._replicate_get_property_groups}
        connection = MockPortalConnection(response_data_maker_by_remote_method)

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
                [StringProperty('twitterhandle', '', '', 'groupb', '')],
                ),
            ]
        eq_(expected_property_groups, retrieved_property_groups)

        self._assert_expected_remote_method_used(connection)

    @classmethod
    def _replicate_get_property_groups(
        cls,
        remote_method,
        body_deserialization,
        ):
        return cls._PROPERTY_GROUP_DATA
