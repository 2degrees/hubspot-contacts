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

from hubspot.connection.exc import HubspotClientError
from hubspot.connection.testing import MockPortalConnection
from nose.tools import assert_raises
from nose.tools import assert_raises_regexp
from nose.tools import eq_
from nose.tools import ok_
from voluptuous import MultipleInvalid

from hubspot.contacts.generic_utils import get_uuid4_str
from hubspot.contacts.properties import BooleanProperty
from hubspot.contacts.properties import DatetimeProperty
from hubspot.contacts.properties import EnumerationProperty
from hubspot.contacts.properties import NumberProperty
from hubspot.contacts.properties import Property
from hubspot.contacts.properties import StringProperty
from hubspot.contacts.properties import create_property
from hubspot.contacts.properties import delete_property
from hubspot.contacts.properties import get_all_properties
from hubspot.contacts.testing import CreateProperty
from hubspot.contacts.testing import DeleteProperty
from hubspot.contacts.testing import GetAllProperties
from hubspot.contacts.testing import UnsuccessfulCreateProperty


STUB_PROPERTY = Property(
    'is_polite',
    'Is contact polite?',
    'Whether the contact is polite',
    'social_interaction',
    'booleancheckbox',
    )

STUB_STRING_PROPERTY = StringProperty.init_from_generalization(STUB_PROPERTY)

STUB_BOOLEAN_PROPERTY = BooleanProperty.init_from_generalization(
    STUB_PROPERTY,
    true_label='Sim',
    false_label='Nao',
    )

STUB_DATETIME_PROPERTY = \
    DatetimeProperty.init_from_generalization(STUB_PROPERTY)

STUB_ENUMERATION_PROPERTY = EnumerationProperty.init_from_generalization(
    STUB_PROPERTY,
    options={'label1': 'value1', 'label2': '123'},
    )

STUB_NUMBER_PROPERTY = NumberProperty.init_from_generalization(STUB_PROPERTY)


class TestGettingAllProperties(object):

    def test_no_properties(self):
        self._check_properties_retrieval([])

    def test_multiple_properties(self):
        properties = [STUB_BOOLEAN_PROPERTY, STUB_DATETIME_PROPERTY]
        self._check_properties_retrieval(properties)

    #{ Property specializations

    def test_boolean(self):
        self._check_properties_retrieval([STUB_BOOLEAN_PROPERTY])

    def test_datetime(self):
        self._check_properties_retrieval([STUB_DATETIME_PROPERTY])

    def test_enumeration(self):
        self._check_properties_retrieval([STUB_ENUMERATION_PROPERTY])

    def test_number(self):
        self._check_properties_retrieval([STUB_NUMBER_PROPERTY])

    def test_string(self):
        self._check_properties_retrieval([STUB_STRING_PROPERTY])

    def _check_properties_retrieval(self, properties):
        api_calls_simulator = GetAllProperties(properties)
        with MockPortalConnection(api_calls_simulator) as connection:
            retrieved_properties = get_all_properties(connection)

        eq_(list(properties), list(retrieved_properties))

    def test_unsupported_type(self):
        api_calls_simulator = _simulate_get_all_properties_with_unsupported_type
        with assert_raises(MultipleInvalid):
            with MockPortalConnection(api_calls_simulator) as connection:
                get_all_properties(connection)

    #}


def _simulate_get_all_properties_with_unsupported_type():
    api_calls = GetAllProperties([STUB_STRING_PROPERTY])()
    for api_call in api_calls:
        for property_data in api_call.response_body_deserialization:
            property_data['type'] = 'invalid_type'
    return api_calls


class TestCreatingProperty(object):

    def test_all_fields_set(self):
        property_ = STUB_NUMBER_PROPERTY
        field_values = property_.get_field_values().values()
        are_all_fields_set = all(field_values)
        ok_(
            are_all_fields_set,
            'This test requires a property with all fields set',
            )

        self._check_create_property(property_, property_)

    def test_enum_options(self):
        self._check_create_property(
            STUB_ENUMERATION_PROPERTY,
            STUB_ENUMERATION_PROPERTY,
            )

    def test_custom_boolean_labels(self):
        self._check_create_property(
            STUB_BOOLEAN_PROPERTY,
            STUB_BOOLEAN_PROPERTY,
            )

    @classmethod
    def _check_create_property(cls, property_, expected_property):
        simulator = CreateProperty(property_)
        with MockPortalConnection(simulator) as connection:
            created_property = create_property(property_, connection)

        eq_(expected_property, created_property)

    def test_unsuccessful_creation(self):
        error_message = 'Whoops!'
        exception = HubspotClientError(error_message, get_uuid4_str())
        simulator = UnsuccessfulCreateProperty(STUB_NUMBER_PROPERTY, exception)
        with assert_raises_regexp(HubspotClientError, error_message):
            with MockPortalConnection(simulator) as connection:
                create_property(STUB_NUMBER_PROPERTY, connection)


def test_successful_property_deletion():
    property_name = 'test'
    simulator = DeleteProperty(property_name)
    with MockPortalConnection(simulator) as connection:
        delete_property(property_name, connection)
