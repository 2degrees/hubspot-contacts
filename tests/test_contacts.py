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

from datetime import date
from datetime import datetime
from decimal import Decimal

from nose.tools import assert_raises_regexp
from nose.tools import eq_
from hubspot.connection.testing import MockPortalConnection

from hubspot.contacts import save_contacts
from hubspot.contacts._constants import BATCH_SAVING_SIZE_LIMIT
from hubspot.contacts.exc import HubspotPropertyValueError
from hubspot.contacts.testing import SaveContacts

from tests._utils import make_contact
from tests._utils import make_contacts
from tests.test_properties import STUB_BOOLEAN_PROPERTY
from tests.test_properties import STUB_DATETIME_PROPERTY
from tests.test_properties import STUB_ENUMERATION_PROPERTY
from tests.test_properties import STUB_NUMBER_PROPERTY
from tests.test_properties import STUB_STRING_PROPERTY


class TestSavingContacts(object):

    def test_no_contacts(self):
        self._check_saved_contacts_match([])

    def test_without_exceeding_batch_size_limit(self):
        contacts = make_contacts(BATCH_SAVING_SIZE_LIMIT)
        self._check_saved_contacts_match(contacts)

    def test_exceeding_batch_size_limit(self):
        contacts = make_contacts(BATCH_SAVING_SIZE_LIMIT + 1)
        self._check_saved_contacts_match(contacts)

    def test_contacts_as_a_generator(self):
        contacts = make_contacts(BATCH_SAVING_SIZE_LIMIT)
        connection = self._make_connection_for_contacts(contacts)

        contacts_generator = iter(contacts)
        with connection:
            save_contacts(contacts_generator, connection)

    def test_property_values_in_request(self):
        property_value = 'true'
        contact = make_contact(1, {STUB_STRING_PROPERTY.name: property_value})
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
        contact = make_contact(1, {property_definition.name: original_value})
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
        saved_contacts = make_contacts(1)
        connection = \
            self._make_connection_for_contacts(saved_contacts, property_)

        contact_with_invalid_property_value = \
            make_contact(1, {property_.name: property_value})
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
