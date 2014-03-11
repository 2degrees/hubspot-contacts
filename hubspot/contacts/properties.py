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


Property = Record.create_type('Property', 'name', 'type', 'options')


_PROPERTY_TYPES = (
    'bool',
    'datetime',
    'enumeration',
    'number',
    'string',
    )

_GET_ALL_PROPERTIES_RESPONSE_SCHEMA_DEFINITION = [
    {
        'name': unicode,
        'type': Any(*_PROPERTY_TYPES),
        'options': [],
        }
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


def _build_property_from_data(property_data):
    property_ = Property(
        property_data['name'],
        property_data['type'],
        property_data['options'],
        )
    return property_
