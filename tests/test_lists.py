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
from abc import abstractproperty
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
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
from hubspot.contacts._constants import BATCH_RETRIEVAL_SIZE_LIMIT
from hubspot.contacts.lists import ContactList
from hubspot.contacts.lists import add_contacts_to_list
from hubspot.contacts.lists import create_static_contact_list
from hubspot.contacts.lists import delete_contact_list
from hubspot.contacts.lists import get_all_contact_lists
from hubspot.contacts.lists import get_all_contacts
from hubspot.contacts.lists import get_all_contacts_by_last_update
from hubspot.contacts.lists import get_all_contacts_from_list
from hubspot.contacts.lists import remove_contacts_from_list
from hubspot.contacts.testing import AddContactsToList
from hubspot.contacts.testing import CreateStaticContactList
from hubspot.contacts.testing import DeleteContactList
from hubspot.contacts.testing import GetAllContactLists
from hubspot.contacts.testing import GetAllContacts
from hubspot.contacts.testing import GetAllContactsByLastUpdate
from hubspot.contacts.testing import GetContactsFromList
from hubspot.contacts.testing import RemoveContactsFromList
from hubspot.contacts.testing import UnsuccessfulCreateStaticContactList

from tests._utils import make_contact
from tests._utils import make_contacts
from tests.test_properties import STUB_BOOLEAN_PROPERTY
from tests.test_properties import STUB_DATETIME_PROPERTY
from tests.test_properties import STUB_ENUMERATION_PROPERTY
from tests.test_properties import STUB_NUMBER_PROPERTY
from tests.test_properties import STUB_PROPERTY
from tests.test_properties import STUB_STRING_PROPERTY


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
        for index in xrange(0, BATCH_RETRIEVAL_SIZE_LIMIT + 1):
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


def test_contact_list_deletion():
    simulator = DeleteContactList(_STUB_CONTACT_LIST.id)
    with MockPortalConnection(simulator) as connection:
        delete_contact_list(_STUB_CONTACT_LIST.id, connection)


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


class _BaseGettingContactsTestCase(object):

    __metaclass__ = ABCMeta

    _RETRIEVER = abstractproperty()

    _SIMULATOR_CLASS = abstractproperty()

    def test_no_contacts(self):
        self._check_retrieved_contacts_match([], [])

    def test_not_exceeding_pagination_size(self):
        contacts_count = BATCH_RETRIEVAL_SIZE_LIMIT - 1
        contacts = make_contacts(contacts_count)
        self._check_retrieved_contacts_match(contacts, contacts)

    @abstractmethod
    def test_exceeding_pagination_size(self):
        pass

    def test_getting_existing_properties(self):
        simulator_contacts = [
            make_contact(1, properties={STUB_PROPERTY.name: 'foo'}),
            make_contact(
                2,
                properties={STUB_PROPERTY.name: 'baz', 'p2': 'bar'},
                ),
            ]

        expected_contacts = _get_contacts_with_stub_property(simulator_contacts)

        self._check_retrieved_contacts_match(
            simulator_contacts,
            expected_contacts,
            property_names=[STUB_PROPERTY.name],
            )

    def test_getting_non_existing_properties(self):
        """Requesting non-existing properties fails silently in HubSpot"""
        contacts = make_contacts(BATCH_RETRIEVAL_SIZE_LIMIT)
        self._check_retrieved_contacts_match(
            contacts,
            contacts,
            property_names=['undefined'],
            )

    def test_contacts_with_related_contact_vids(self):
        contacts = [make_contact(1, related_contact_vids=[2, 3])]
        self._check_retrieved_contacts_match(contacts, contacts)

    #{ Property type casting

    def test_property_type_casting(self):
        test_cases_data = [
            (STUB_BOOLEAN_PROPERTY, 'true', True),
            (
                STUB_DATETIME_PROPERTY,
                u'1396607280140',
                datetime(2014, 4, 4, 10, 28, 0, 140000),
                ),
            (STUB_ENUMERATION_PROPERTY, 'value1', 'value1'),
            (STUB_NUMBER_PROPERTY, '1.01', Decimal('1.01')),
            (STUB_STRING_PROPERTY, u'value', u'value'),
            ]

        for property_, raw_value, expected_value in test_cases_data:
            retrieved_contact = self._retrieve_contact_with_stub_property(
                property_,
                raw_value,
                )
            retrieved_property_value = \
                retrieved_contact.properties[property_.name]

            yield eq_, expected_value, retrieved_property_value

    def _retrieve_contact_with_stub_property(
        self,
        property_definition,
        property_value_raw,
        **kwargs
        ):
        simulator_contact = \
            make_contact(1, {property_definition.name: property_value_raw})
        property_names = [property_definition.name]
        connection = self._make_connection_for_contacts(
            contacts=[simulator_contact],
            available_property=property_definition,
            property_names=property_names,
            **kwargs
            )

        with connection:
            # Trigger API calls by consuming iterator
            retrieved_contacts = list(
                self._RETRIEVER(
                    connection,
                    property_names=property_names,
                    **kwargs
                    ),
                )

        retrieved_contact = retrieved_contacts[0]
        return retrieved_contact

    def test_property_type_casting_for_unknown_property(self):
        simulator_contact = make_contact(1, {'p1': 'yes'})
        expected_contact = simulator_contact.copy()
        expected_contact.properties = {}
        self._check_retrieved_contacts_match(
            [simulator_contact],
            [expected_contact],
            )

    #}

    def _check_retrieved_contacts_match(
        self,
        simulator_contacts,
        expected_contacts,
        **kwargs
        ):
        connection = \
            self._make_connection_for_contacts(simulator_contacts, **kwargs)

        with connection:
            # Trigger API calls by consuming iterator
            retrieved_contacts = list(self._RETRIEVER(connection, **kwargs))

        eq_(list(expected_contacts), retrieved_contacts)

    @classmethod
    def _make_connection_for_contacts(
        cls,
        contacts,
        available_property=None,
        **simulator_kwargs
        ):
        available_property = available_property or STUB_STRING_PROPERTY
        simulator = cls._SIMULATOR_CLASS(
            contacts=contacts,
            available_properties=[available_property],
            **simulator_kwargs
            )
        connection = MockPortalConnection(simulator)
        return connection


def _get_contacts_with_stub_property(contacts):
    contacts_with_stub_property = []
    for contact in contacts:
        contact_with_stub_property = Contact(
            contact.vid,
            contact.email_address,
            {STUB_PROPERTY.name: contact.properties[STUB_PROPERTY.name]},
            [],
            )
        contacts_with_stub_property.append(contact_with_stub_property)

    return contacts_with_stub_property


class TestGettingAllContacts(_BaseGettingContactsTestCase):

    _RETRIEVER = staticmethod(get_all_contacts)

    _SIMULATOR_CLASS = GetAllContacts

    def test_exceeding_pagination_size(self):
        contacts_count = BATCH_RETRIEVAL_SIZE_LIMIT + 1
        contacts = make_contacts(contacts_count)
        self._check_retrieved_contacts_match(contacts, contacts)


class TestGettingAllContactsByLastUpdate(_BaseGettingContactsTestCase):

    _RETRIEVER = staticmethod(get_all_contacts_by_last_update)

    _SIMULATOR_CLASS = GetAllContactsByLastUpdate

    def test_exceeding_pagination_size(self):
        contacts = make_contacts(BATCH_RETRIEVAL_SIZE_LIMIT + 1)
        self._check_retrieved_contacts_match(contacts, contacts)

    def test_duplicated_contacts(self):
        contact1, contact2 = make_contacts(2)
        expected_contacts = [contact1, contact2]
        simulator_contacts = [contact1, contact2, contact1]

        self._check_retrieved_contacts_match(
            simulator_contacts,
            expected_contacts,
            )

    def test_single_page_with_cutoff(self):
        contacts = make_contacts(BATCH_RETRIEVAL_SIZE_LIMIT - 1)
        page_1_contact_2 = contacts[1]
        self._check_retrieved_contacts_are_newer_than_contact(
            page_1_contact_2,
            contacts,
            )

    def test_multiple_pages_with_cutoff_on_first_page(self):
        contacts = make_contacts(BATCH_RETRIEVAL_SIZE_LIMIT + 1)
        page_1_last_contact = contacts[BATCH_RETRIEVAL_SIZE_LIMIT - 1]
        self._check_retrieved_contacts_are_newer_than_contact(
            page_1_last_contact,
            contacts,
            )

    def test_multiple_pages_with_cutoff_on_subsequent_page(self):
        contacts = make_contacts(BATCH_RETRIEVAL_SIZE_LIMIT + 2)
        page_2_contact_2 = contacts[BATCH_RETRIEVAL_SIZE_LIMIT + 1]
        self._check_retrieved_contacts_are_newer_than_contact(
            page_2_contact_2,
            contacts,
            )

    def test_cutoff_newer_than_most_recently_updated_contact(self):
        contacts = make_contacts(BATCH_RETRIEVAL_SIZE_LIMIT - 1)
        page_1_contact_1 = contacts[0]
        self._check_retrieved_contacts_are_newer_than_contact(
            page_1_contact_1,
            contacts,
            )

    def _check_retrieved_contacts_are_newer_than_contact(
        self,
        contact,
        simulator_contacts,
        ):
        contact_added_at_datetime = \
            self._SIMULATOR_CLASS.get_contact_added_at_datetime(
                contact,
                simulator_contacts,
                )
        cutoff_datetime = contact_added_at_datetime + timedelta(milliseconds=1)

        contact_index = simulator_contacts.index(contact)
        expected_contacts = simulator_contacts[:contact_index]

        self._check_retrieved_contacts_match(
            simulator_contacts,
            expected_contacts,
            cutoff_datetime=cutoff_datetime,
            )


class TestGettingAllContactsFromList(_BaseGettingContactsTestCase):

    _RETRIEVER = staticmethod(get_all_contacts_from_list)

    _SIMULATOR_CLASS = GetContactsFromList

    def test_exceeding_pagination_size(self):
        contacts_count = BATCH_RETRIEVAL_SIZE_LIMIT + 1
        contacts = make_contacts(contacts_count)
        self._check_retrieved_contacts_match(contacts, contacts)

    def _check_retrieved_contacts_match(
        self,
        simulator_contacts,
        expected_contacts,
        **kwargs
        ):
        kwargs.setdefault('contact_list', _STUB_CONTACT_LIST)

        super_ = super(TestGettingAllContactsFromList, self)
        super_._check_retrieved_contacts_match(
            simulator_contacts,
            expected_contacts,
            **kwargs
            )

    def _retrieve_contact_with_stub_property(
        self,
        property_definition,
        property_value_raw,
        **kwargs
        ):
        kwargs.setdefault('contact_list', _STUB_CONTACT_LIST)

        super_ = super(TestGettingAllContactsFromList, self)
        retrieved_contact = super_._retrieve_contact_with_stub_property(
            property_definition,
            property_value_raw,
            **kwargs
            )
        return retrieved_contact
