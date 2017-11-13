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

from datetime import datetime
from datetime import timedelta
from os import environ
from unittest.case import SkipTest

from hubspot.connection import APIKey
from hubspot.connection import PortalConnection
from nose.tools import assert_in
from nose.tools import assert_is_none
from nose.tools import assert_items_equal
from nose.tools import assert_not_in
from nose.tools import eq_

from hubspot.contacts import save_contacts
from hubspot.contacts.lists import add_contacts_to_list
from hubspot.contacts.lists import create_static_contact_list
from hubspot.contacts.lists import delete_contact_list
from hubspot.contacts.lists import get_all_contact_lists
from hubspot.contacts.lists import get_all_contacts
from hubspot.contacts.lists import get_all_contacts_by_last_update
from hubspot.contacts.lists import get_all_contacts_from_list
from hubspot.contacts.lists import remove_contacts_from_list
from hubspot.contacts.properties import StringProperty
from hubspot.contacts.properties import create_property
from hubspot.contacts.properties import delete_property
from hubspot.contacts.properties import get_all_properties
from hubspot.contacts.property_groups import PropertyGroup
from hubspot.contacts.property_groups import create_property_group
from hubspot.contacts.property_groups import delete_property_group
from hubspot.contacts.property_groups import get_all_property_groups

_CHANGE_SOURCE = __name__

_SMOKE_TEST_API_KEY_ENVIRON_KEY = 'SMOKE_TEST_API_KEY'


def test_properties():
    with _get_portal_connection() as connection:
        all_property_groups = get_all_property_groups(connection)
        first_property_group = all_property_groups[0]
        property_to_create = StringProperty(
            'propertytest',
            'Property Test',
            'Just a test property',
            first_property_group.name,
            'text',
        )
        created_property = create_property(property_to_create, connection)
        eq_(property_to_create, created_property)

        all_properties = get_all_properties(connection)
        assert_in(created_property, all_properties)

        delete_property(created_property.name, connection)

        all_properties = get_all_properties(connection)
        assert_not_in(created_property, all_properties)


def test_property_groups():
    with _get_portal_connection() as connection:
        property_group_to_create = PropertyGroup('propertygrouptest')
        created_property_group = \
            create_property_group(property_group_to_create, connection)
        eq_(property_group_to_create.name, created_property_group.name)

        all_property_groups = get_all_property_groups(connection)
        assert_in(created_property_group, all_property_groups)

        delete_property_group(created_property_group.name, connection)

        all_property_groups = get_all_property_groups(connection)
        assert_not_in(created_property_group, all_property_groups)


def test_static_lists():
    with _get_portal_connection() as connection:
        new_contact_list_name = 'contactlisttest'
        created_static_list = \
            create_static_contact_list(new_contact_list_name, connection)
        eq_(new_contact_list_name, created_static_list.name)

        all_contact_lists = get_all_contact_lists(connection)
        assert_in(created_static_list, all_contact_lists)

        all_contacts = get_all_contacts(connection)
        first_contact = next(all_contacts)
        added_contact_vids = add_contacts_to_list(
            created_static_list,
            [first_contact],
            connection,
        )
        assert_in(first_contact.vid, added_contact_vids)

        contacts_in_list = list(
            get_all_contacts_from_list(connection, created_static_list)
        )
        assert_in(first_contact, contacts_in_list)

        removed_contact_vids = remove_contacts_from_list(
            created_static_list,
            [first_contact],
            connection,
        )
        assert_in(first_contact.vid, removed_contact_vids)

        contacts_in_list = list(
            get_all_contacts_from_list(connection, created_static_list)
        )
        assert_not_in(first_contact, contacts_in_list)

        delete_contact_list(created_static_list.id, connection)

        all_contact_lists = get_all_contact_lists(connection)
        assert_not_in(created_static_list, all_contact_lists)


def test_getting_all_contacts():
    with _get_portal_connection() as connection:
        all_contacts = get_all_contacts(connection)
        first_contact = next(all_contacts)
        assert_in('lastmodifieddate', first_contact.properties)

        requested_property_names = ('email',)
        all_contacts = get_all_contacts(
            connection,
            property_names=requested_property_names,
        )
        first_contact = next(all_contacts)

        expected_property_names = \
            ('lastmodifieddate',) + requested_property_names
        assert_items_equal(
            expected_property_names,
            first_contact.properties.keys(),
        )


def test_getting_all_contacts_by_last_update():
    with _get_portal_connection() as connection:
        _update_random_contact(connection)  # Force an update

        all_contacts = get_all_contacts_by_last_update(connection)
        first_contact = next(all_contacts)
        assert_in('lastmodifieddate', first_contact.properties)

        requested_property_names = ('email',)
        all_contacts = get_all_contacts_by_last_update(
            connection,
            property_names=requested_property_names,
        )
        first_contact = next(all_contacts)
        expected_property_names = \
            ('lastmodifieddate',) + requested_property_names
        assert_items_equal(
            expected_property_names,
            first_contact.properties.keys(),
        )

        contacts_from_future = get_all_contacts_by_last_update(
            connection,
            property_names=requested_property_names,
            cutoff_datetime=datetime.now() + timedelta(days=100),
        )
        eq_([], list(contacts_from_future))


def test_save_contacts():
    with _get_portal_connection() as connection:
        result = _update_random_contact(connection)
        assert_is_none(result)


def _update_random_contact(connection):
    all_contacts = get_all_contacts(connection)
    first_contact = next(all_contacts)

    del first_contact.properties['lastmodifieddate']
    first_contact.properties['lastname'] = 'First User'

    return save_contacts([first_contact], connection)


def _get_api_key():
    try:
        api_key_value = environ[_SMOKE_TEST_API_KEY_ENVIRON_KEY]
    except KeyError:
        raise SkipTest(
            '{!r} is not available in env'.format(
                _SMOKE_TEST_API_KEY_ENVIRON_KEY,
            ),
        )

    api_key = APIKey(api_key_value)
    return api_key


def _get_portal_connection():
    api_key = _get_api_key()
    connection = PortalConnection(api_key, _CHANGE_SOURCE)
    return connection
