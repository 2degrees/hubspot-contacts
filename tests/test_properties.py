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

from functools import partial

from nose.tools import assert_raises
from nose.tools import eq_
from voluptuous import MultipleInvalid

from hubspot.contacts.properties import BooleanProperty
from hubspot.contacts.properties import DatetimeProperty
from hubspot.contacts.properties import EnumerationProperty
from hubspot.contacts.properties import NumberProperty
from hubspot.contacts.properties import PROPERTY_TYPE_BY_NAME
from hubspot.contacts.properties import Property
from hubspot.contacts.properties import StringProperty
from hubspot.contacts.properties import get_all_properties

from tests.utils import BaseMethodTestCase
from tests.utils import RemoteMethod
from tests.utils.connection import MockPortalConnection


_PROPERTY_TYPE_NAME_BY_PROPERTY_TYPE = \
    {type_: type_name  for type_name, type_ in PROPERTY_TYPE_BY_NAME.items()}


_STUB_PROPERTY = Property(
    'is_polite',
    'Is contact polite?',
    'Whether the contact is polite',
    'social_interaction',
    'booleancheckbox',
    )


class TestGettingAllProperties(BaseMethodTestCase):

    _REMOTE_METHOD = RemoteMethod('/properties', 'GET')

    def test_no_properties(self):
        response_maker = lambda request_data: []
        connection = MockPortalConnection(response_maker)

        retrieved_properties = get_all_properties(connection)
        self._assert_expected_remote_method_used(connection)

        eq_(0, len(retrieved_properties))

    def test_multiple_properties(self):
        properties = [
            BooleanProperty.init_from_generalization(_STUB_PROPERTY),
            DatetimeProperty.init_from_generalization(_STUB_PROPERTY),
            ]
        response_maker = partial(
            _replicate_get_all_properties_response_data,
            properties,
            )
        connection = MockPortalConnection(response_maker)

        retrieved_properties = get_all_properties(connection)

        self._assert_expected_remote_method_used(connection)

        eq_(properties, retrieved_properties)


class TestPropertyTypes(object):

    def test_boolean(self):
        boolean_property = \
            BooleanProperty.init_from_generalization(_STUB_PROPERTY)
        self._check_property_retrieval(boolean_property)

    def test_datetime(self):
        datetime_property = \
            DatetimeProperty.init_from_generalization(_STUB_PROPERTY)
        self._check_property_retrieval(datetime_property)

    def test_enumeration(self):
        enumeration_property = EnumerationProperty.init_from_generalization(
            _STUB_PROPERTY,
            options={'label1': 'value1', 'label2': 'value2'},
            )
        self._check_property_retrieval(enumeration_property)

    def test_number(self):
        number_property = \
            NumberProperty.init_from_generalization(_STUB_PROPERTY)
        self._check_property_retrieval(number_property)

    def test_string(self):
        string_property = \
            StringProperty.init_from_generalization(_STUB_PROPERTY)
        self._check_property_retrieval(string_property)

    def _check_property_retrieval(self, property_):
        response_maker = \
            partial(_replicate_get_all_properties_response_data, [property_])
        connection = MockPortalConnection(response_maker)

        retrieved_properties = get_all_properties(connection)

        eq_(1, len(retrieved_properties))
        eq_(property_, retrieved_properties[0])

    def test_unsupported_type(self):
        connection = MockPortalConnection(
            _replicate_get_all_properties_invalid_response_data,
            )

        assert_raises(
            MultipleInvalid,
            get_all_properties,
            connection,
            )


def _replicate_get_all_properties_response_data(properties, request_data):
    properties_data = []
    for property_ in properties:
        property_type = _get_property_type_name(property_)
        property_options = _get_raw_property_options(property_)
        property_data = {
            'name': property_.name,
            'label': property_.label,
            'description': property_.description,
            'groupName': property_.group_name,
            'fieldType': property_.field_widget,
            'type': property_type,
            'options': property_options,
            }

        properties_data.append(property_data)

    return properties_data


def _get_property_type_name(property_):
    property_type = property_.__class__
    property_type_name = _PROPERTY_TYPE_NAME_BY_PROPERTY_TYPE[property_type]
    return property_type_name


def _get_raw_property_options(property_):
    if isinstance(property_, BooleanProperty):
        raw_options_data = [
                {'label': 'True', 'value': 'true', 'displayOrder': 0},
                {'label': 'False', 'value': 'false', 'displayOrder': 1},
            ]
    elif isinstance(property_, EnumerationProperty):
        raw_options_data = []
        for option_label, option_value in property_.options.items():
            option_data = {
                'label': option_label,
                'value': option_value,
                'displayOrder': 0,
                }
            raw_options_data.append(option_data)
    else:
        raw_options_data = []

    return raw_options_data


def _replicate_get_all_properties_invalid_response_data(request_data):
    properties = [{
        'name': 'name',
        'label': 'label',
        'description': 'description',
        'groupName': 'group_name',
        'fieldType': 'field_widget',
        'type': 'invalid_type',
        'options': [],
        }]
    return properties
