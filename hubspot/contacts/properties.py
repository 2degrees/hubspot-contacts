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

from pyrecord import Record
from voluptuous import Any
from voluptuous import Schema

from hubspot.contacts.generic_utils import remove_unset_values_from_dict


Property = Record.create_type(
    'Property',
    'name',
    'label',
    'description',
    'group_name',
    'field_widget',
    )

BooleanProperty = Property.extend_type('BooleanProperty')

DatetimeProperty = Property.extend_type('DatetimeProperty')

EnumerationProperty = Property.extend_type('EnumerationProperty', 'options')

NumberProperty = Property.extend_type('NumberProperty')

StringProperty = Property.extend_type('StringProperty')


PROPERTY_TYPE_BY_NAME = {
    'bool': BooleanProperty,
    'datetime': DatetimeProperty,
    'enumeration': EnumerationProperty,
    'number': NumberProperty,
    'string': StringProperty,
    }

_PROPERTY_TYPE_NAME_BY_PROPERTY_TYPE = \
    {type_: type_name  for type_name, type_ in PROPERTY_TYPE_BY_NAME.items()}


_PROPERTY_RESPONSE_SCHEMA_DEFINITION = {
    'name': unicode,
    'type': Any(*PROPERTY_TYPE_BY_NAME.keys()),
    'options': [],
    }

_CREATE_PROPERTY_RESPONSE_SCHEMA = Schema(
    _PROPERTY_RESPONSE_SCHEMA_DEFINITION,
    required=True,
    extra=True,
    )


_GET_ALL_PROPERTIES_RESPONSE_SCHEMA_DEFINITION = [
    _PROPERTY_RESPONSE_SCHEMA_DEFINITION,
    ]


_GET_ALL_PROPERTIES_RESPONSE_SCHEMA = Schema(
    _GET_ALL_PROPERTIES_RESPONSE_SCHEMA_DEFINITION,
    required=True,
    extra=True,
    )


def get_all_properties(connection):
    properties_data = connection.send_get_request('/properties')
    _GET_ALL_PROPERTIES_RESPONSE_SCHEMA(properties_data)

    properties = []
    for property_data in properties_data:
        property_ = _build_property_from_data(property_data)
        properties.append(property_)
    return properties


def create_property(property_, connection):
    property_type = get_property_type_name(property_)
    property_options = get_raw_property_options(property_)
    request_body_deserialization = {
        'name': property_.name,
        'label': property_.label,
        'description': property_.description,
        'groupName': property_.group_name,
        'fieldType': property_.field_widget,
        'type': property_type,
        'options': property_options,
        }
    request_body_deserialization = \
        remove_unset_values_from_dict(request_body_deserialization)

    response_data = connection.send_put_request(
        '/properties/' + property_.name,
        request_body_deserialization,
        )

    property_data = _CREATE_PROPERTY_RESPONSE_SCHEMA(response_data)
    created_property = _build_property_from_data(property_data)
    return created_property


def delete_property(property_name, connection):
    connection.send_delete_request('/properties/' + property_name)


def get_property_type_name(property_):
    property_type = property_.__class__
    property_type_name = _PROPERTY_TYPE_NAME_BY_PROPERTY_TYPE[property_type]
    return property_type_name


def get_raw_property_options(property_):
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


def _build_property_from_data(property_data):
    property_type_name = property_data['type']
    property_type = PROPERTY_TYPE_BY_NAME[property_type_name]

    if issubclass(property_type, EnumerationProperty):
        enumeration_options_data = property_data['options']
        enumeration_options = \
            _build_enumeration_options_from_data(enumeration_options_data)
        additional_field_values = {'options': enumeration_options}
    else:
        additional_field_values = {}

    property_ = property_type(
        property_data['name'],
        property_data['label'],
        property_data['description'],
        property_data['groupName'],
        property_data['fieldType'],
        **additional_field_values
        )
    return property_


def _build_enumeration_options_from_data(enumeration_options_data):
    enumeration_options = {}
    for option_data in enumeration_options_data:
        option_label = option_data['label']
        option_value = option_data['value']
        enumeration_options[option_label] = option_value
    return enumeration_options
