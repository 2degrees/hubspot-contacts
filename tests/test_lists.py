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

from inspect import isgenerator

from nose.tools import assert_items_equal
from nose.tools import assert_raises
from nose.tools import eq_
from nose.tools import ok_
from voluptuous import Invalid
from hubspot.connection.exc import HubspotClientError
from hubspot.connection.testing import ConstantResponseDataMaker
from hubspot.connection.testing import MockPortalConnection
from hubspot.connection.testing import RemoteMethod

from hubspot.contacts import Contact
from hubspot.contacts.lists import ContactList
from hubspot.contacts.lists import add_contacts_to_list
from hubspot.contacts.lists import create_static_contact_list
from hubspot.contacts.lists import get_all_contact_lists

from tests.utils import BaseMethodTestCase


_STUB_CONTACT_LIST_DATA = {
    'listId': 1,
    'name': 'atestlist',
    'dynamic': False,
    }

_STUB_CONTACT_LIST = ContactList(
    _STUB_CONTACT_LIST_DATA['listId'],
    _STUB_CONTACT_LIST_DATA['name'],
    _STUB_CONTACT_LIST_DATA['dynamic'],
    )


_STUB_CONTACT_1 = Contact(1, 'dude@bro.com', {}, [])

_STUB_CONTACT_2 = Contact(2, 'bro@bro.com', {}, [])


class TestContactListsRetrieval(BaseMethodTestCase):

    _REMOTE_METHOD = RemoteMethod('/contacts/v1/lists', 'GET')

    def test_no_contact_lists(self):
        connection = self._make_connection_with_contact_lists([])

        contact_lists = get_all_contact_lists(connection)

        self._assert_expected_remote_method_used(connection)

        eq_([], list(contact_lists))
        ok_(len(connection.remote_method_invocations))

    def test_getting_existing_contact_lists(self):
        connection = self._make_connection_with_contact_lists(
            [_STUB_CONTACT_LIST_DATA],
            )

        contact_lists = get_all_contact_lists(connection)
        contact_lists = list(contact_lists)

        self._assert_expected_remote_method_used(connection)

        expected_contact_lists = [_STUB_CONTACT_LIST]
        eq_(expected_contact_lists, contact_lists)

        ok_(len(connection.remote_method_invocations))

    def test_is_generator(self):
        connection = self._make_connection_with_contact_lists([])

        contact_lists = get_all_contact_lists(connection)
        ok_(isgenerator(contact_lists))

    def _make_connection_with_contact_lists(self, contact_lists):
        response_data = {'has-more': False, 'offset': 9, 'lists': contact_lists}
        connection = MockPortalConnection({
            self._REMOTE_METHOD: ConstantResponseDataMaker(response_data),
            })
        return connection


class TestStaticContactListCreation(BaseMethodTestCase):

    _REMOTE_METHOD = RemoteMethod('/contacts/v1/lists', 'POST')

    def test_name_doesnt_exist(self):
        connection = MockPortalConnection({
            self._REMOTE_METHOD: ConstantResponseDataMaker(
                _STUB_CONTACT_LIST_DATA,
                ),
            })

        contact_list = create_static_contact_list(
            _STUB_CONTACT_LIST.name,
            connection,
            )

        eq_(1, len(connection.remote_method_invocations))
        self._assert_expected_remote_method_used(connection)

        expected_body_deserialization = \
            {'name': _STUB_CONTACT_LIST.name, 'dynamic': False}
        body_deserialization = \
            connection.remote_method_invocations[0].body_deserialization
        eq_(expected_body_deserialization, body_deserialization)

        eq_(_STUB_CONTACT_LIST, contact_list)

    def test_name_already_exists(self):
        connection = MockPortalConnection({
            self._REMOTE_METHOD: _raise_hubspot_client_error,
            })

        with assert_raises(HubspotClientError):
            create_static_contact_list(_STUB_CONTACT_LIST.name, connection)

        eq_(1, len(connection.remote_method_invocations))
        self._assert_expected_remote_method_used(connection)


class TestAddingContactsToList(BaseMethodTestCase):

    _REMOTE_METHOD = RemoteMethod(
        '/lists/{}/add'.format(_STUB_CONTACT_LIST.id),
        'POST',
        )

    def test_no_contacts(self):
        connection = MockPortalConnection({})

        added_contact_vids = \
            add_contacts_to_list(_STUB_CONTACT_LIST, [], connection)

        eq_(0, len(connection.remote_method_invocations))
        eq_([], added_contact_vids)

    def test_contacts_not_in_list(self):
        self._test_contact_addition(
            expected_updated_contacts=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_to_add=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_list=[],
            )

    def test_contacts_already_in_list(self):
        self._test_contact_addition(
            expected_updated_contacts=[],
            contacts_to_add=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_list=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            )

    def test_some_contacts_already_in_list(self):
        self._test_contact_addition(
            expected_updated_contacts=[_STUB_CONTACT_2],
            contacts_to_add=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_list=[_STUB_CONTACT_1],
            )

    def test_non_existing_contact(self):
        self._test_contact_addition(
            expected_updated_contacts=[],
            contacts_to_add=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_hubspot=[],
            )

    def test_non_existing_list(self):
        connection = MockPortalConnection({
            self._REMOTE_METHOD: _raise_hubspot_client_error,
            })

        with assert_raises(HubspotClientError):
            add_contacts_to_list(
                _STUB_CONTACT_LIST,
                [_STUB_CONTACT_1, _STUB_CONTACT_2],
                connection,
                )

        eq_(1, len(connection.remote_method_invocations))
        self._assert_expected_remote_method_used(connection)

    def test_unexpected_response(self):
        connection = MockPortalConnection({
            self._REMOTE_METHOD: ConstantResponseDataMaker({'update': []}),
            })

        with assert_raises(Invalid):
            add_contacts_to_list(
                _STUB_CONTACT_LIST,
                [_STUB_CONTACT_1, _STUB_CONTACT_2],
                connection,
                )

    def _test_contact_addition(
        self,
        expected_updated_contacts,
        contacts_to_add,
        contacts_in_list=None,
        contacts_in_hubspot=None,
        ):
        if contacts_in_list is None:
            contacts_in_list = []
        if contacts_in_hubspot is None:
            contacts_in_hubspot = [_STUB_CONTACT_1, _STUB_CONTACT_2]

        contacts_not_in_list = set(contacts_to_add) - set(contacts_in_list)
        updated_contacts = set(contacts_in_hubspot) & contacts_not_in_list
        connection = self._make_connection(updated_contacts)

        added_contact_vids = add_contacts_to_list(
            _STUB_CONTACT_LIST,
            contacts_to_add,
            connection,
            )

        eq_(1, len(connection.remote_method_invocations))
        self._assert_expected_remote_method_used(connection)

        contact_vids_to_add = _get_contact_vids(contacts_to_add)
        expected_body_deserialization = {'vids': contact_vids_to_add}
        body_deserialization = \
            connection.remote_method_invocations[0].body_deserialization
        eq_(expected_body_deserialization, body_deserialization)

        expected_updated_contact_vids = \
            _get_contact_vids(expected_updated_contacts)
        assert_items_equal(expected_updated_contact_vids, added_contact_vids)

    def _make_connection(self, updated_contacts=None):
        updated_contacts = _get_contact_vids(updated_contacts or [])
        response_data = {'updated': updated_contacts}
        response_data_maker = ConstantResponseDataMaker(response_data)
        connection = \
            MockPortalConnection({self._REMOTE_METHOD: response_data_maker})
        return connection


def _raise_hubspot_client_error(query_string_args, body_deserialization):
    raise HubspotClientError('Empty string will do', 1)


def _get_contact_vids(contacts):
    return [c.vid for c in contacts]
