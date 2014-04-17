# coding: utf-8
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
from datetime import date
from datetime import datetime
from datetime import timedelta
from decimal import Decimal

from nose.tools import assert_raises_regexp
from nose.tools import eq_
from hubspot.connection.testing import MockPortalConnection

from hubspot.contacts import Contact
from hubspot.contacts import get_all_contacts
from hubspot.contacts import get_all_contacts_by_last_update
from hubspot.contacts import save_contacts
from hubspot.contacts._batching_limits import HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT
from hubspot.contacts._batching_limits import HUBSPOT_BATCH_SAVING_SIZE_LIMIT
from hubspot.contacts.exc import HubspotPropertyValueError
from hubspot.contacts.generic_utils import get_uuid4_str
from hubspot.contacts.testing import GetAllContacts
from hubspot.contacts.testing import GetAllContactsByLastUpdate
from hubspot.contacts.testing import SaveContacts

from tests.test_properties import STUB_BOOLEAN_PROPERTY
from tests.test_properties import STUB_DATETIME_PROPERTY
from tests.test_properties import STUB_ENUMERATION_PROPERTY
from tests.test_properties import STUB_NUMBER_PROPERTY
from tests.test_properties import STUB_PROPERTY
from tests.test_properties import STUB_STRING_PROPERTY


class _BaseGettingAllContactsTestCase(object):

    __metaclass__ = ABCMeta

    _RETRIEVER = abstractproperty()

    _SIMULATOR_CLASS = abstractproperty()

    def test_no_contacts(self):
        self._check_retrieved_contacts_match([], [])

    def test_not_exceeding_pagination_size(self):
        contacts_count = HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT - 1
        contacts = _make_contacts(contacts_count)
        self._check_retrieved_contacts_match(contacts, contacts)

    @abstractmethod
    def test_exceeding_pagination_size(self):
        pass

    def test_getting_existing_properties(self):
        simulator_contacts = [
            _make_contact(1, properties={STUB_PROPERTY.name: 'foo'}),
            _make_contact(
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
        contacts = _make_contacts(HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT)
        self._check_retrieved_contacts_match(
            contacts,
            contacts,
            property_names=['undefined'],
            )

    def test_contacts_with_related_contact_vids(self):
        contacts = [_make_contact(1, related_contact_vids=[2, 3])]
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
        ):
        simulator_contact = \
            _make_contact(1, {property_definition.name: property_value_raw})
        property_names = [property_definition.name]
        connection = self._make_connection_for_contacts(
            [simulator_contact],
            property_definition,
            property_names=property_names,
            )

        with connection:
            # Trigger API calls by consuming iterator
            retrieved_contacts = \
                list(self._RETRIEVER(connection, property_names))

        retrieved_contact = retrieved_contacts[0]
        return retrieved_contact

    def test_property_type_casting_for_unknown_property(self):
        simulator_contact = _make_contact(1, {'p1': 'yes'})
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
            contacts,
            [available_property],
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


class TestGettingAllContacts(_BaseGettingAllContactsTestCase):

    _RETRIEVER = staticmethod(get_all_contacts)

    _SIMULATOR_CLASS = GetAllContacts

    def test_exceeding_pagination_size(self):
        contacts_count = HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT + 1
        contacts = _make_contacts(contacts_count)
        self._check_retrieved_contacts_match(contacts, contacts)


class TestGettingAllContactsByLastUpdate(_BaseGettingAllContactsTestCase):

    _RETRIEVER = staticmethod(get_all_contacts_by_last_update)

    _SIMULATOR_CLASS = GetAllContactsByLastUpdate

    def test_exceeding_pagination_size(self):
        contacts = _make_contacts(HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT + 1)
        self._check_retrieved_contacts_match(contacts, contacts)

    def test_duplicated_contacts(self):
        contact1, contact2 = _make_contacts(2)
        expected_contacts = [contact1, contact2]
        simulator_contacts = [contact1, contact2, contact1]

        self._check_retrieved_contacts_match(
            simulator_contacts,
            expected_contacts,
            )

    def test_single_page_with_cutoff(self):
        contacts = _make_contacts(HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT - 1)
        page_1_contact_2 = contacts[1]
        self._check_retrieved_contacts_are_newer_than_contact(
            page_1_contact_2,
            contacts,
            )

    def test_multiple_pages_with_cutoff_on_first_page(self):
        contacts = _make_contacts(HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT + 1)
        page_1_last_contact = contacts[HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT - 1]
        self._check_retrieved_contacts_are_newer_than_contact(
            page_1_last_contact,
            contacts,
            )

    def test_multiple_pages_with_cutoff_on_subsequent_page(self):
        contacts = _make_contacts(HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT + 2)
        page_2_contact_2 = contacts[HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT + 1]
        self._check_retrieved_contacts_are_newer_than_contact(
            page_2_contact_2,
            contacts,
            )

    def test_cutoff_newer_than_most_recently_updated_contact(self):
        contacts = _make_contacts(HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT - 1)
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


class TestSavingContacts(object):

    def test_no_contacts(self):
        self._check_saved_contacts_match([])

    def test_without_exceeding_batch_size_limit(self):
        contacts = _make_contacts(HUBSPOT_BATCH_SAVING_SIZE_LIMIT)
        self._check_saved_contacts_match(contacts)

    def test_exceeding_batch_size_limit(self):
        contacts = _make_contacts(HUBSPOT_BATCH_SAVING_SIZE_LIMIT + 1)
        self._check_saved_contacts_match(contacts)

    def test_contacts_as_a_generator(self):
        contacts = _make_contacts(HUBSPOT_BATCH_SAVING_SIZE_LIMIT)
        connection = self._make_connection_for_contacts(contacts)

        contacts_generator = iter(contacts)
        with connection:
            save_contacts(contacts_generator, connection)

    def test_property_values_in_request(self):
        property_value = 'true'
        contact = _make_contact(1, {STUB_STRING_PROPERTY.name: property_value})
        self._check_saved_contacts_match([contact])

    def test_property_type_casting(self):
        test_cases_data = [
            (STUB_BOOLEAN_PROPERTY, True, u'true'),
            (STUB_BOOLEAN_PROPERTY, False, u'false'),
            (STUB_BOOLEAN_PROPERTY, 'text', u'true'),
            (STUB_BOOLEAN_PROPERTY, '', u'false'),
            (
                STUB_DATETIME_PROPERTY,
                datetime(2014, 4, 4, 10, 28, 0, 140000),
                u'1396607280140',
                ),
            (STUB_DATETIME_PROPERTY, date(2014, 4, 4), u'1396569600000'),
            (STUB_ENUMERATION_PROPERTY, u'value1', u'value1'),
            (STUB_ENUMERATION_PROPERTY, 123, u'123'),
            (STUB_NUMBER_PROPERTY, Decimal('123.01'), u'123.01'),
            (STUB_NUMBER_PROPERTY, 123, u'123'),
            (STUB_NUMBER_PROPERTY, '123', u'123'),
            (STUB_STRING_PROPERTY, u'valúe', u'valúe'),
            (STUB_STRING_PROPERTY, 'value', u'value'),
            (STUB_STRING_PROPERTY, 123, u'123'),
            ]

        for property_, original_value, expected_value in test_cases_data:
            yield (
                self._assert_property_value_cast_equals,
                property_,
                original_value,
                expected_value,
                )

    def _assert_property_value_cast_equals(
        self,
        property_definition,
        original_value,
        expected_cast_value,
        ):
        contact = _make_contact(1, {property_definition.name: original_value})
        contacts = [contact]
        connection = \
            self._make_connection_for_contacts(contacts, property_definition)
        with connection:
            save_contacts(contacts, connection)

        api_call = connection.api_calls[-1]
        contact_data = api_call.request_body_deserialization[0]
        contact_properties_data = contact_data['properties']
        contact_property_data = contact_properties_data[0]
        eq_(expected_cast_value, contact_property_data['value'])

    def test_invalid_property_values(self):
        test_cases_data = [
            (STUB_DATETIME_PROPERTY, 1396603680140, '{} is not a date'),
            (STUB_NUMBER_PROPERTY, 'abc', '{} is not a number'),
            ]
        for property_, property_value, exc_message_template in test_cases_data:
            yield (
                self._test_invalid_property_value,
                property_,
                property_value,
                exc_message_template,
                )

    def _test_invalid_property_value(
        self,
        property_,
        property_value,
        exc_message_template,
        ):
        saved_contacts = []
        connection = \
            self._make_connection_for_contacts(saved_contacts, property_)

        contact_with_invalid_property_value = \
            _make_contact(1, {property_.name: property_value})
        exc_message = exc_message_template.format(repr(property_value))
        with assert_raises_regexp(HubspotPropertyValueError, exc_message):
            with connection:
                save_contacts([contact_with_invalid_property_value], connection)

    @classmethod
    def _check_saved_contacts_match(cls, contacts, available_property=None):
        connection = \
            cls._make_connection_for_contacts(contacts, available_property)
        with connection:
            save_contacts(contacts, connection)

    @staticmethod
    def _make_connection_for_contacts(contacts, available_property=None):
        available_property = available_property or STUB_STRING_PROPERTY
        simulator = SaveContacts(contacts, [available_property])
        connection = MockPortalConnection(simulator)
        return connection


def _make_contacts(count):
    contacts = []
    for contact_vid in range(1, count + 1):
        contact = _make_contact(contact_vid)
        contacts.append(contact)
    return contacts


def _make_contact(vid, properties=None, related_contact_vids=None):
    properties = properties or {}
    related_contact_vids = related_contact_vids or []
    email_address = _get_random_email_address()
    contact = Contact(vid, email_address, properties, related_contact_vids)
    return contact


def _get_random_email_address():
    email_user_name = get_uuid4_str()
    email_address = email_user_name + '@example.com'
    return email_address
