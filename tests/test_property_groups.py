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

from hubspot.connection.exc import HubspotClientError
from hubspot.connection.testing import MockPortalConnection
from hubspot.connection.testing import RemoteMethod

from hubspot.contacts.generic_utils import get_uuid4_str
from hubspot.contacts.properties import DatetimeProperty
from hubspot.contacts.properties import StringProperty
from hubspot.contacts.property_groups import PropertyGroup
from hubspot.contacts.property_groups import create_property_group
from hubspot.contacts.property_groups import get_all_property_groups
from hubspot.contacts.testing import AllPropertyGroupsRetrievalResponseDataMaker
from hubspot.contacts.testing import PropertyGroupCreationResponseDataMaker

from tests.utils import BaseMethodTestCase


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
            self._REMOTE_METHOD: \
                PropertyGroupCreationResponseDataMaker(property_group),
            }
        connection = MockPortalConnection(response_data_maker_by_remote_method)

        created_property_group = \
            create_property_group(property_group, connection)

        self._assert_expected_remote_method_used(connection)

        eq_(1, len(connection.remote_method_invocations))
        remote_method_invocation = connection.remote_method_invocations[0]

        return remote_method_invocation, created_property_group


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

    _STUB_PROPERTY = DatetimeProperty('lastmodifieddate', '', '', 'groupa', '')

    def test_no_property_groups(self):
        self._test_retrieved_property_group_equal([])

    def test_property_groups_without_display_name(self):
        property_group = PropertyGroup('groupa', '', [self._STUB_PROPERTY])
        self._test_retrieved_property_group_equal([property_group])

    def test_property_groups_without_properties(self):
        property_group = PropertyGroup('groupa', 'Group A')
        self._test_retrieved_property_group_equal([property_group])

    def test_multiple_property_groups(self):
        property_groups = [
            PropertyGroup('groupa', 'Group A', [self._STUB_PROPERTY]),
            PropertyGroup(
                'groupb',
                'Group B',
                [StringProperty('twitterhandle', '', '', 'groupb', '')],
                ),
            ]
        self._test_retrieved_property_group_equal(property_groups)

    def _test_retrieved_property_group_equal(self, property_groups):
        connection = self._make_connection_for_property_groups(property_groups)
        self._assert_retrieved_property_groups_match(
            property_groups,
            connection,
            )

    def _make_connection_for_property_groups(self, property_groups):
        response_data_maker = \
            AllPropertyGroupsRetrievalResponseDataMaker(property_groups)
        response_data_maker_by_remote_method = \
            {self._REMOTE_METHOD: response_data_maker}
        connection = MockPortalConnection(response_data_maker_by_remote_method)
        return connection

    def _assert_retrieved_property_groups_match(
        self,
        expected_property_groups,
        connection,
        ):
        retrieved_property_groups = get_all_property_groups(connection)

        eq_(expected_property_groups, retrieved_property_groups)

        self._assert_expected_remote_method_used(connection)
