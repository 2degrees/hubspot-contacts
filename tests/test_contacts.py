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

from abc import abstractmethod
from abc import abstractproperty
from datetime import date
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from nose.tools import assert_dict_contains_subset
from nose.tools import assert_in
from nose.tools import assert_raises_regexp
from nose.tools import eq_

from hubspot.connection.testing import ConstantResponseDataMaker
from hubspot.connection.testing import MockPortalConnection
from hubspot.connection.testing import RemoteMethod
from hubspot.contacts import Contact
from hubspot.contacts import get_all_contacts
from hubspot.contacts import get_all_contacts_by_last_update
from hubspot.contacts import save_contacts
from hubspot.contacts._batching_limits import HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT
from hubspot.contacts._batching_limits import HUBSPOT_BATCH_SAVING_SIZE_LIMIT
from hubspot.contacts.exc import HubspotPropertyValueError
from hubspot.contacts.generic_utils import \
    convert_timestamp_in_milliseconds_to_datetime
from hubspot.contacts.generic_utils import get_uuid4_str
from hubspot.contacts.testing import AllContactsRetrievalResponseDataMaker
from hubspot.contacts.testing import AllPropertiesRetrievalResponseDataMaker
from hubspot.contacts.testing import CONTACT_SAVING_RESPONSE_DATA_MAKER
from hubspot.contacts.testing import \
    RecentlyUpdatedContactsRetrievalResponseDataMaker

from tests.test_properties import PROPERTIES_RETRIEVAL_REMOTE_METHOD
from tests.test_properties import STUB_BOOLEAN_PROPERTY
from tests.test_properties import STUB_DATETIME_PROPERTY
from tests.test_properties import STUB_ENUMERATION_PROPERTY
from tests.test_properties import STUB_NUMBER_PROPERTY
from tests.test_properties import STUB_PROPERTY
from tests.test_properties import STUB_STRING_PROPERTY
from tests.utils import BaseMethodTestCase


_STUB_TIMESTAMP = 12345


class _BaseContactsTestCase(BaseMethodTestCase):

    def _make_connection(
        self,
        remote_method_response_data_maker,
        property_retrieval_response_data_maker,
        ):
        response_data_maker_by_remote_method = {
            self._REMOTE_METHOD: remote_method_response_data_maker,
            PROPERTIES_RETRIEVAL_REMOTE_METHOD:
                property_retrieval_response_data_maker,
            }
        return MockPortalConnection(response_data_maker_by_remote_method)


class _BaseGettingAllContactsTestCase(_BaseContactsTestCase):

    _RETRIEVER = abstractproperty()

    _RESPONSE_DATA_MAKER = abstractproperty()

    def test_no_contacts(self):
        connection = self._make_connection_for_contacts([])

        self._assert_retrieved_contacts_match([], connection)

        contacts_retrieval_remote_method_invocations = \
            connection.get_invocations_for_remote_method(self._REMOTE_METHOD)
        eq_(1, len(contacts_retrieval_remote_method_invocations))

    def test_not_exceeding_pagination_size(self):
        contacts_count = HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT - 1
        expected_contacts = _make_contacts(contacts_count)
        connection = self._make_connection_for_contacts(expected_contacts)

        self._assert_retrieved_contacts_match(expected_contacts, connection)

        contacts_retrieval_remote_method_invocations = \
            connection.get_invocations_for_remote_method(self._REMOTE_METHOD)
        eq_(1, len(contacts_retrieval_remote_method_invocations))

    @abstractmethod
    def test_exceeding_pagination_size(self):
        pass

    def test_getting_existing_properties(self):
        expected_contacts = [
            _make_contact(1, properties={STUB_PROPERTY.name: 'foo'}),
            _make_contact(
                2,
                properties={STUB_PROPERTY.name: 'baz', 'p2': 'bar'},
                ),
            ]
        connection = self._make_connection_for_contacts(expected_contacts)

        expected_contacts_with_expected_properties = []
        for original_contact in expected_contacts:
            expected_contact_with_expected_properties = Contact(
                original_contact.vid,
                original_contact.email_address,
                {
                    STUB_PROPERTY.name:
                        original_contact.properties[STUB_PROPERTY.name],
                    },
                [],
                )
            expected_contacts_with_expected_properties.append(
                expected_contact_with_expected_properties,
                )

        property_names = (STUB_PROPERTY.name,)
        self._assert_retrieved_contacts_match(
            expected_contacts_with_expected_properties,
            connection,
            property_names=property_names,
            )

        contacts_retrieval_remote_method_invocations = \
            connection.get_invocations_for_remote_method(self._REMOTE_METHOD)
        eq_(1, len(contacts_retrieval_remote_method_invocations))

        remote_method_invocation = \
            contacts_retrieval_remote_method_invocations[0]
        eq_(2, len(remote_method_invocation.query_string_args))
        assert_in('property', remote_method_invocation.query_string_args)
        eq_(
            property_names,
            remote_method_invocation.query_string_args['property'],
            )

    def test_getting_non_existing_properties(self):
        """Requesting non-existing properties fails silently in HubSpot"""
        expected_contacts = _make_contacts(HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT)
        connection = self._make_connection_for_contacts(expected_contacts)

        self._assert_retrieved_contacts_match(expected_contacts, connection)

        contacts_retrieval_remote_method_invocations = \
            connection.get_invocations_for_remote_method(self._REMOTE_METHOD)
        eq_(1, len(contacts_retrieval_remote_method_invocations))

    def test_contacts_with_sub_contacts(self):
        expected_sub_contacts = [2, 3]
        expected_contacts = _make_contact(1, sub_contacts=expected_sub_contacts)
        connection = self._make_connection_for_contacts([expected_contacts])

        retrieved_contacts = self._RETRIEVER(connection)
        eq_(expected_sub_contacts, list(retrieved_contacts)[0].sub_contacts)

    def test_contacts_without_sub_contacts(self):
        expected_sub_contacts = []
        expected_contacts = _make_contact(1, sub_contacts=expected_sub_contacts)
        connection = self._make_connection_for_contacts([expected_contacts])

        retrieved_contacts = self._RETRIEVER(connection)
        eq_(expected_sub_contacts, list(retrieved_contacts)[0].sub_contacts)

    def _assert_retrieved_contacts_match(
        self,
        expected_contacts,
        connection,
        *args,
        **kwargs
        ):
        retrieved_contacts = self._RETRIEVER(connection, *args, **kwargs)
        eq_(list(expected_contacts), list(retrieved_contacts))

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
        contact = \
            _make_contact(1, {property_definition.name: property_value_raw})
        property_retrieval_response_data_maker = \
            AllPropertiesRetrievalResponseDataMaker([property_definition])
        connection = self._make_connection_for_contacts(
            [contact],
            property_retrieval_response_data_maker,
            )

        retrieved_contacts = \
            self._RETRIEVER(connection, [property_definition.name])
        retrieved_contacts = list(retrieved_contacts)

        retrieved_contact = retrieved_contacts[0]
        return retrieved_contact

    def test_property_type_casting_for_unknown_property(self):
        contact = _make_contact(1, {'p1': 'yes'})
        connection = self._make_connection_for_contacts([contact])

        retrieved_contacts = self._RETRIEVER(connection)
        retrieved_contacts = list(retrieved_contacts)

        retrieved_contact = retrieved_contacts[0]
        eq_(0, len(retrieved_contact.properties))

    #}

    def _make_connection_for_contacts(
        self,
        contacts,
        property_retrieval_response_data_maker=None,
        ):
        contacts_retrieval_response_data_maker = \
            self._RESPONSE_DATA_MAKER(contacts)
        if not property_retrieval_response_data_maker:
            property_retrieval_response_data_maker = \
                AllPropertiesRetrievalResponseDataMaker([STUB_STRING_PROPERTY])

        connection = self._make_connection(
            contacts_retrieval_response_data_maker,
            property_retrieval_response_data_maker,
            )
        return connection


class TestGettingAllContacts(_BaseGettingAllContactsTestCase):

    _REMOTE_METHOD = RemoteMethod('/lists/all/contacts/all', 'GET')

    _RETRIEVER = staticmethod(get_all_contacts)

    _RESPONSE_DATA_MAKER = AllContactsRetrievalResponseDataMaker

    def test_exceeding_pagination_size(self):
        contacts_count = HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT + 1
        expected_contacts = _make_contacts(contacts_count)
        connection = self._make_connection_for_contacts(expected_contacts)

        self._assert_retrieved_contacts_match(expected_contacts, connection)

        contacts_retrieval_remote_method_invocations = \
            connection.get_invocations_for_remote_method(self._REMOTE_METHOD)
        eq_(2, len(contacts_retrieval_remote_method_invocations))

        remote_method_invocation2 = \
            contacts_retrieval_remote_method_invocations[1]
        eq_(2, len(remote_method_invocation2.query_string_args))

        assert_in('vidOffset', remote_method_invocation2.query_string_args)
        page1_last_contact = \
            expected_contacts[HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT - 1]
        expect_vid_offset = page1_last_contact.vid
        eq_(
            expect_vid_offset,
            remote_method_invocation2.query_string_args['vidOffset'],
            )


class TestGettingAllContactsByLastUpdate(_BaseGettingAllContactsTestCase):

    _REMOTE_METHOD = \
        RemoteMethod('/lists/recently_updated/contacts/recent', 'GET')

    _RETRIEVER = staticmethod(get_all_contacts_by_last_update)

    _RESPONSE_DATA_MAKER = RecentlyUpdatedContactsRetrievalResponseDataMaker

    def test_exceeding_pagination_size(self):
        contacts_count = HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT + 1
        expected_contacts = _make_contacts(contacts_count)
        connection = self._make_connection_for_contacts(expected_contacts)

        self._assert_retrieved_contacts_match(expected_contacts, connection)

        contacts_retrieval_remote_method_invocations = \
            connection.get_invocations_for_remote_method(self._REMOTE_METHOD)
        eq_(2, len(contacts_retrieval_remote_method_invocations))

        remote_method_invocation2 = \
            contacts_retrieval_remote_method_invocations[1]
        eq_(3, len(remote_method_invocation2.query_string_args))

        page1_last_contact = \
            expected_contacts[HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT - 1]
        page1_last_contact_added_at = \
            _STUB_TIMESTAMP - HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT
        expected_query_string_args = {
            'vidOffset': page1_last_contact.vid,
            'timeOffset': page1_last_contact_added_at,
            }
        assert_dict_contains_subset(
            expected_query_string_args,
            remote_method_invocation2.query_string_args,
            )

    def test_duplicated_contacts(self):
        two_contacts = _make_contacts(2)
        expected_contacts = two_contacts + two_contacts[:1]

        connection = self._make_connection_for_contacts(expected_contacts)

        self._assert_retrieved_contacts_match(two_contacts, connection)

    def test_cutoff_single_page(self):
        self._check_cutoff_positioning(5, 10)

    def test_cutoff_multiple_page_cutoff_on_first_page(self):
        self._check_cutoff_positioning(5, 150)

    def test_cutoff_multiple_page_cutoff_on_subsequent_page(self):
        self._check_cutoff_positioning(102, 150)

    def _check_cutoff_positioning(self, cutoff_index, contact_count):
        stub_datetime = \
            convert_timestamp_in_milliseconds_to_datetime(_STUB_TIMESTAMP)
        cutoff_datetime = stub_datetime - timedelta(milliseconds=cutoff_index)

        expected_contacts = _make_contacts(contact_count)

        connection = self._make_connection_for_contacts(expected_contacts)

        retrieved_contacts = \
            self._RETRIEVER(connection, cutoff_datetime=cutoff_datetime)
        retrieved_contacts = list(retrieved_contacts)

        expected_number_of_contacts = cutoff_index
        eq_(expected_number_of_contacts, len(retrieved_contacts))


class TestSavingContacts(_BaseContactsTestCase):

    _REMOTE_METHOD = RemoteMethod('/contact/batch/', 'POST')

    def setup(self):
        self.connection = \
            self._make_connection_for_property_definition(STUB_STRING_PROPERTY)

    def test_no_contacts(self):
        contacts_generator = iter([])
        save_contacts(contacts_generator, self.connection)

        remote_method_invocations = \
            self._get_remote_method_invocations(self.connection)
        eq_(0, len(remote_method_invocations))

    def test_without_exceeding_batch_size_limit(self):
        contacts = _make_contacts(HUBSPOT_BATCH_SAVING_SIZE_LIMIT)

        contacts_generator = iter(contacts)
        save_contacts(contacts_generator, self.connection)

        expected_body_deserialization = \
            [{'email': c.email_address, 'properties': []} for c in contacts]
        remote_method_invocation = \
            self._get_sole_remote_method_invocation(self.connection)
        eq_(
            expected_body_deserialization,
            remote_method_invocation.body_deserialization,
            )

    def test_exceeding_batch_size_limit(self):
        contacts = _make_contacts(HUBSPOT_BATCH_SAVING_SIZE_LIMIT + 1)

        contacts_generator = iter(contacts)
        save_contacts(contacts_generator, self.connection)

        remote_method_invocations = \
            self._get_remote_method_invocations(self.connection)
        eq_(2, len(remote_method_invocations))

        contacts1 = contacts[:HUBSPOT_BATCH_SAVING_SIZE_LIMIT]
        remote_method_invocation1 = remote_method_invocations[0]
        self._assert_contacts_sent_in_request(
            contacts1,
            remote_method_invocation1,
            )

        contacts2 = contacts[HUBSPOT_BATCH_SAVING_SIZE_LIMIT:]
        remote_method_invocation2 = remote_method_invocations[1]
        self._assert_contacts_sent_in_request(
            contacts2,
            remote_method_invocation2,
            )

    def test_contacts_as_a_list(self):
        contacts = _make_contacts(HUBSPOT_BATCH_SAVING_SIZE_LIMIT)

        save_contacts(contacts, self.connection)

        remote_method_invocation = \
            self._get_sole_remote_method_invocation(self.connection)
        self._assert_contacts_sent_in_request(
            contacts,
            remote_method_invocation,
            )

    @staticmethod
    def _assert_contacts_sent_in_request(contacts, remote_method_invocation):
        contacts_data = _format_contacts_data_for_saving(contacts)
        eq_(contacts_data, remote_method_invocation.body_deserialization)

    def test_property_values_in_request(self):
        property_value = 'true'
        contact = _make_contact(1, {STUB_STRING_PROPERTY.name: property_value})
        connection = \
            self._make_connection_for_property_definition(STUB_STRING_PROPERTY)

        save_contacts([contact], connection)

        remote_method_invocation = \
            self._get_sole_remote_method_invocation(connection)
        contact_properties_data = \
            remote_method_invocation.body_deserialization[0]['properties']
        expected_contact_properties_data = \
            [{'property': STUB_STRING_PROPERTY.name, 'value': property_value}]
        eq_(expected_contact_properties_data, contact_properties_data)

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
        connection = \
            self._make_connection_for_property_definition(property_definition)

        save_contacts([contact], connection)

        remote_method_invocation = \
            self._get_sole_remote_method_invocation(connection)
        expected_contact = contact.copy()
        expected_contact.properties = \
            {property_definition.name: expected_cast_value}
        self._assert_contacts_sent_in_request(
            [expected_contact],
            remote_method_invocation,
            )

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
        contact = _make_contact(1, {property_.name: property_value})
        connection = self._make_connection_for_property_definition(property_)

        exc_message = exc_message_template.format(repr(property_value))
        with assert_raises_regexp(HubspotPropertyValueError, exc_message):
            save_contacts([contact], connection)

    def _make_connection_for_property_definition(self, property_definition):
        property_retrieval_response_data_maker = \
            AllPropertiesRetrievalResponseDataMaker([property_definition])
        connection = self._make_connection(
            CONTACT_SAVING_RESPONSE_DATA_MAKER,
            property_retrieval_response_data_maker,
            )
        return connection

    def _get_sole_remote_method_invocation(self, connection):
        remote_method_invocations = \
            self._get_remote_method_invocations(connection)
        eq_(1, len(remote_method_invocations))
        remote_method_invocation = remote_method_invocations[0]
        return remote_method_invocation

    def _get_remote_method_invocations(self, connection):
        remote_method_invocations = \
            connection.get_invocations_for_remote_method(self._REMOTE_METHOD)
        return remote_method_invocations


def _format_contacts_data_for_saving(contacts):
    contacts_data = [_format_contact_data_for_saving(c) for c in contacts]
    return contacts_data


def _format_contact_data_for_saving(contact):
    contact_data = {
        'email': contact.email_address,
        'properties': _format_contact_properties_for_saving(contact.properties),
        }
    return contact_data


def _format_contact_properties_for_saving(contact_properties):
    contact_properties_data = [
        {'property': n, 'value': v} for n, v in contact_properties.items()
        ]
    return contact_properties_data


def _make_contacts(count):
    contacts = []
    for contact_vid in range(1, count + 1):
        contact = _make_contact(contact_vid)
        contacts.append(contact)
    return contacts


def _make_contact(vid, properties=None, sub_contacts=None):
    properties = properties or {}
    sub_contacts = sub_contacts or []
    email_address = _get_random_email_address()
    contact = Contact(vid, email_address, properties, sub_contacts)
    return contact


def _get_random_email_address():
    email_user_name = get_uuid4_str()
    email_address = email_user_name + '@example.com'
    return email_address
