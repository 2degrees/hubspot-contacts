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


Property = Record.create_type(
    'Property',
    'name',
    'label',
    'description',
    'group_name',
    'field_widget',
    )

BooleanProperty = Property.extend_type(
    'BooleanProperty',
    'true_label',
    'false_label',
    true_label='Yes',
    false_label='No',
    )

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


def get_all_properties(connection):
    from hubspot.contacts._schemas.properties import \
        GET_ALL_PROPERTIES_RESPONSE_SCHEMA

    properties_data = connection.send_get_request('/properties')
    GET_ALL_PROPERTIES_RESPONSE_SCHEMA(properties_data)

    properties = []
    for property_data in properties_data:
        property_ = _build_property_from_data(property_data)
        properties.append(property_)
    return properties


def create_property(property_, connection):
    from hubspot.contacts._schemas.properties import \
        CREATE_PROPERTY_RESPONSE_SCHEMA
    from hubspot.contacts.request_data_formatters.properties import \
        format_data_for_property

    request_body_deserialization = format_data_for_property(property_)

    response_data = connection.send_put_request(
        '/properties/' + property_.name,
        request_body_deserialization,
        )

    property_data = CREATE_PROPERTY_RESPONSE_SCHEMA(response_data)
    created_property = _build_property_from_data(property_data)
    return created_property


def delete_property(property_name, connection):
    connection.send_delete_request('/properties/' + property_name)


def _build_property_from_data(property_data):
    property_type_name = property_data['type']
    property_type = PROPERTY_TYPE_BY_NAME[property_type_name]

    if issubclass(property_type, EnumerationProperty):
        enumeration_options_data = property_data['options']
        enumeration_options = \
            _build_enumeration_options_from_data(enumeration_options_data)
        additional_field_values = {'options': enumeration_options}

    elif issubclass(property_type, BooleanProperty):
        additional_field_values = \
            _build_boolean_additional_field_values(property_data['options'])

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


def _build_boolean_additional_field_values(boolean_options_data):
    additional_field_values = {}
    for option_data in boolean_options_data:
        option_value = option_data['value']
        if option_value == 'true':
            additional_field_values['true_label'] = option_data['label']

        elif option_value == 'false':
            additional_field_values['false_label'] = option_data['label']

        else:
            assert False, '{!r} is not a valid bool option'.format(option_value)

    assert 2 == len(additional_field_values), \
        'Boolean properties must have exactly 2 options'

    return additional_field_values
