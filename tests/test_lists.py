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

from hubspot.connection.exc import HubspotClientError
from hubspot.connection.testing import MockPortalConnection
from nose.tools import assert_items_equal
from nose.tools import assert_raises
from nose.tools import assert_raises_regexp
from nose.tools import eq_
from nose.tools import ok_
from voluptuous import Invalid

from hubspot.contacts import Contact
from hubspot.contacts._batching_limits import HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT
from hubspot.contacts.lists import ContactList
from hubspot.contacts.lists import add_contacts_to_list
from hubspot.contacts.lists import create_static_contact_list
from hubspot.contacts.lists import get_all_contact_lists
from hubspot.contacts.lists import remove_contacts_from_list
from hubspot.contacts.testing import AddContactsToList
from hubspot.contacts.testing import CreateStaticContactList
from hubspot.contacts.testing import GetAllContactLists
from hubspot.contacts.testing import RemoveContactsFromList
from hubspot.contacts.testing import UnsuccessfulCreateStaticContactList


_STUB_CONTACT_LIST = ContactList(1, 'atestlist', False)

_STUB_CONTACT_1 = Contact(1, 'dude@bro.com', {}, [])

_STUB_CONTACT_2 = Contact(2, 'bro@bro.com', {}, [])


class TestContactListsRetrieval(object):

    def test_no_contact_lists(self):
        with self._make_connection_with_contact_lists([]) as connection:
            contact_lists = list(get_all_contact_lists(connection))

        eq_([], contact_lists)

    def test_getting_existing_contact_lists_single_page(self):
        contact_lists = [_STUB_CONTACT_LIST]
        connection = self._make_connection_with_contact_lists(contact_lists)

        with connection:
            retrieved_contact_lists = list(get_all_contact_lists(connection))

        eq_(contact_lists, retrieved_contact_lists)

    def test_getting_existing_contact_lists_multiple_pages(self):
        contact_lists = []
        for index in xrange(0, HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT + 1):
            contact_list = ContactList(
                index,
                'list{}'.format(index),
                True,
                )
            contact_lists.append(contact_list)

        connection = self._make_connection_with_contact_lists(contact_lists)
        with connection:
            retrieved_contact_lists = list(get_all_contact_lists(connection))

        eq_(contact_lists, retrieved_contact_lists)

    def test_is_generator(self):
        connection = self._make_connection_with_contact_lists([])

        contact_lists = get_all_contact_lists(connection)
        ok_(isgenerator(contact_lists))

    def test_unexpected_response(self):
        connection = MockPortalConnection(
            _simulate_get_all_contact_lists_with_unsupported_response,
            )

        with assert_raises(Invalid):
            with connection:
                list(get_all_contact_lists(connection))

    def _make_connection_with_contact_lists(self, contact_lists):
        simulator = GetAllContactLists(contact_lists)
        connection = MockPortalConnection(simulator)
        return connection


def _simulate_get_all_contact_lists_with_unsupported_response():
    api_calls = GetAllContactLists([_STUB_CONTACT_LIST])()
    for api_call in api_calls:
        for list_data in api_call.response_body_deserialization['lists']:
            del list_data['dynamic']
    return api_calls


class TestStaticContactListCreation(object):

    def test_name_doesnt_exist(self):
        simulator = CreateStaticContactList(_STUB_CONTACT_LIST.name)
        with MockPortalConnection(simulator) as connection:
            contact_list = create_static_contact_list(
                _STUB_CONTACT_LIST.name,
                connection,
                )

        eq_(_STUB_CONTACT_LIST, contact_list)

    def test_name_already_exists(self):
        exception = HubspotClientError('Whoops!', 1)
        simulator = UnsuccessfulCreateStaticContactList(
            _STUB_CONTACT_LIST.name,
            exception,
            )

        with assert_raises_regexp(HubspotClientError, str(exception)):
            with MockPortalConnection(simulator) as connection:
                create_static_contact_list(_STUB_CONTACT_LIST.name, connection)

    def test_unexpected_response(self):
        connection = MockPortalConnection(
            _simulate_create_static_contact_list_with_unsupported_response,
            )

        with assert_raises(Invalid):
            with connection:
                create_static_contact_list(_STUB_CONTACT_LIST.name, connection)


def _simulate_create_static_contact_list_with_unsupported_response():
    api_calls = CreateStaticContactList(_STUB_CONTACT_LIST.name)()
    for api_call in api_calls:
        created_contact_list_data = api_call.response_body_deserialization
        del created_contact_list_data['dynamic']

    return api_calls


class TestAddingContactsToList(object):

    def test_no_contacts_to_add(self):
        simulator = AddContactsToList(_STUB_CONTACT_LIST, [], [])

        with MockPortalConnection(simulator) as connection:
            added_contacts_vids = \
                add_contacts_to_list(_STUB_CONTACT_LIST, [], connection)

        eq_([], added_contacts_vids)

    def test_contacts_not_in_list(self):
        self._test_contacts_addition(
            expected_updated_contacts=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_to_add=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_list=[],
            )

    def test_contacts_already_in_list(self):
        self._test_contacts_addition(
            expected_updated_contacts=[],
            contacts_to_add=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_list=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            )

    def test_some_contacts_already_in_list(self):
        self._test_contacts_addition(
            expected_updated_contacts=[_STUB_CONTACT_2],
            contacts_to_add=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_list=[_STUB_CONTACT_1],
            )

    def test_non_existing_contact(self):
        self._test_contacts_addition(
            expected_updated_contacts=[],
            contacts_to_add=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_hubspot=[],
            )

    def test_unexpected_response(self):
        connection = MockPortalConnection(
            _make_unsupported_api_call_from_simulator(AddContactsToList),
            )

        with assert_raises(Invalid):
            with connection:
                add_contacts_to_list(
                    _STUB_CONTACT_LIST,
                    [_STUB_CONTACT_1, _STUB_CONTACT_2],
                    connection,
                    )

    def _test_contacts_addition(
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

        connection = self._make_connection(contacts_to_add, updated_contacts)
        with connection:
            added_contact_vids = add_contacts_to_list(
                _STUB_CONTACT_LIST,
                contacts_to_add,
                connection,
                )

        expected_updated_contact_vids = \
            _get_contact_vids(expected_updated_contacts)
        assert_items_equal(expected_updated_contact_vids, added_contact_vids)

    def _make_connection(self, contacts_to_add, updated_contacts=None):
        updated_contacts = updated_contacts or []
        simulator = AddContactsToList(
            _STUB_CONTACT_LIST,
            contacts_to_add,
            updated_contacts,
            )
        connection = MockPortalConnection(simulator)
        return connection


class TestRemovingContactsFromList(object):

    def test_no_contacts_to_remove(self):
        simulator = RemoveContactsFromList(_STUB_CONTACT_LIST, [], [])

        with MockPortalConnection(simulator) as connection:
            removed_contacts_vids = \
                remove_contacts_from_list(_STUB_CONTACT_LIST, [], connection)

        eq_([], removed_contacts_vids)


    def test_contacts_not_in_list(self):
        self._test_contacts_removal(
            expected_updated_contacts=[],
            contacts_to_remove=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_list=[],
            )

    def test_contacts_in_list(self):
        self._test_contacts_removal(
            expected_updated_contacts=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_to_remove=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_list=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            )

    def test_some_contacts_in_list(self):
        self._test_contacts_removal(
            expected_updated_contacts=[_STUB_CONTACT_1],
            contacts_to_remove=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_list=[_STUB_CONTACT_1],
            )

    def test_non_existing_contact(self):
        self._test_contacts_removal(
            expected_updated_contacts=[],
            contacts_to_remove=[_STUB_CONTACT_1, _STUB_CONTACT_2],
            contacts_in_hubspot=[],
            )

    def test_unexpected_response(self):
        connection = MockPortalConnection(
            _make_unsupported_api_call_from_simulator(RemoveContactsFromList)
            )

        with assert_raises(Invalid):
            remove_contacts_from_list(
                _STUB_CONTACT_LIST,
                [_STUB_CONTACT_1, _STUB_CONTACT_2],
                connection,
                )

    def _test_contacts_removal(
        self,
        expected_updated_contacts,
        contacts_to_remove,
        contacts_in_list=None,
        contacts_in_hubspot=None,
        ):
        if contacts_in_list is None:
            contacts_in_list = []
        if contacts_in_hubspot is None:
            contacts_in_hubspot = [_STUB_CONTACT_1, _STUB_CONTACT_2]

        updated_contacts = set(contacts_in_hubspot) & set(contacts_in_list)
        connection = self._make_connection(contacts_to_remove, updated_contacts)
        with connection:
            removed_contact_vids = remove_contacts_from_list(
                _STUB_CONTACT_LIST,
                contacts_to_remove,
                connection,
                )

        expected_updated_contact_vids = \
            _get_contact_vids(expected_updated_contacts)
        assert_items_equal(expected_updated_contact_vids, removed_contact_vids)

    def _make_connection(self, contacts_to_remove, updated_contacts=None):
        updated_contacts = updated_contacts or []
        simulator = RemoveContactsFromList(
            _STUB_CONTACT_LIST,
            contacts_to_remove,
            updated_contacts,
            )
        connection = MockPortalConnection(simulator)
        return connection


def _make_unsupported_api_call_from_simulator(simulator_class):
    api_calls_simulator = simulator_class(
        _STUB_CONTACT_LIST,
        [_STUB_CONTACT_1, _STUB_CONTACT_2],
        [],
        )

    api_calls = api_calls_simulator()
    for api_call in api_calls:
        response_body_deserialization = api_call.response_body_deserialization
        response_body_deserialization['update'] = \
            response_body_deserialization.pop('updated')

    return lambda: api_calls


def _get_contact_vids(contacts):
    return [c.vid for c in contacts]
