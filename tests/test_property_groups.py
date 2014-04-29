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

from nose.tools import assert_is_none
from nose.tools import assert_raises_regexp
from nose.tools import eq_
from hubspot.connection.exc import HubspotClientError
from hubspot.connection.testing import MockPortalConnection

from hubspot.contacts.generic_utils import get_uuid4_str
from hubspot.contacts.properties import StringProperty
from hubspot.contacts.property_groups import PropertyGroup
from hubspot.contacts.property_groups import create_property_group
from hubspot.contacts.property_groups import delete_property_group
from hubspot.contacts.property_groups import get_all_property_groups
from hubspot.contacts.testing import CreatePropertyGroup
from hubspot.contacts.testing import DeletePropertyGroup
from hubspot.contacts.testing import GetAllPropertyGroups
from hubspot.contacts.testing import UnsuccessfulCreatePropertyGroup

from tests.test_properties import STUB_STRING_PROPERTY


class TestPropertyGroupCreation(object):

    _PROPERTY_GROUP_NAME = 'test-property-group'

    def test_display_name_specified(self):
        property_group = \
            PropertyGroup(self._PROPERTY_GROUP_NAME, 'Test Property Group')

        created_property_group = self._create_property_group(property_group)

        eq_(property_group, created_property_group)

    def test_display_name_not_specified(self):
        property_group = PropertyGroup(self._PROPERTY_GROUP_NAME)

        created_property_group = self._create_property_group(property_group)

        eq_('', created_property_group.display_name)

    def test_unsuccessful_creation(self):
        property_group = PropertyGroup(self._PROPERTY_GROUP_NAME)
        exception = HubspotClientError('Whoops!', get_uuid4_str())
        simulator = UnsuccessfulCreatePropertyGroup(property_group, exception)
        with assert_raises_regexp(HubspotClientError, str(exception)):
            with MockPortalConnection(simulator) as connection:
                create_property_group(property_group, connection)

    @staticmethod
    def _create_property_group(property_group):
        simulator = CreatePropertyGroup(property_group)
        with MockPortalConnection(simulator) as connection:
            created_property_group = \
                create_property_group(property_group, connection)
        return created_property_group


class TestGettingAllPropertyGroups(object):

    _STUB_GROUP_NAME = 'groupa'

    _STUB_PROPERTY = STUB_STRING_PROPERTY.copy()
    _STUB_PROPERTY.group_name = _STUB_GROUP_NAME

    def test_no_property_groups(self):
        self._test_retrieved_property_group_equal([])

    def test_property_groups_without_display_name(self):
        property_group = \
            PropertyGroup(self._STUB_GROUP_NAME, '', [self._STUB_PROPERTY])
        self._test_retrieved_property_group_equal([property_group])

    def test_property_groups_without_properties(self):
        property_group = PropertyGroup(self._STUB_GROUP_NAME, 'Group A')
        self._test_retrieved_property_group_equal([property_group])

    def test_multiple_property_groups(self):
        property_groups = [
            PropertyGroup(
                self._STUB_GROUP_NAME,
                'Group A',
                [self._STUB_PROPERTY],
                ),
            PropertyGroup(
                'groupb',
                'Group B',
                [StringProperty('twitterhandle', '', '', 'groupb', '')],
                ),
            ]
        self._test_retrieved_property_group_equal(property_groups)

    def _test_retrieved_property_group_equal(self, property_groups):
        simulator = GetAllPropertyGroups(property_groups)
        with MockPortalConnection(simulator) as connection:
            retrieved_property_groups = get_all_property_groups(connection)

        eq_(property_groups, retrieved_property_groups)


def test_property_group_deletion():
    property_group_name = 'property_group_name'
    simulator = DeletePropertyGroup(property_group_name)
    with MockPortalConnection(simulator) as connection:
        assert_is_none(delete_property_group(property_group_name, connection))
