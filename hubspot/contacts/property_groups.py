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
from voluptuous import Optional
from voluptuous import Schema

from hubspot.contacts.properties import _build_property_from_data


PropertyGroup = Record.create_type(
    'PropertyGroup',
    'name',
    'display_name',
    'properties',
    display_name=None,
    properties=None,
    )


_PROPERTY_GROUP_CREATION_SCHEMA = Schema(
    {'name': unicode, 'displayName': unicode},
    required=True,
    extra=True,
    )


_PROPERTY_SCHEMA = {}

_PROPERTY_GROUPS_RETRIEVAL_SCHEMA = Schema(
    [{
        'name': unicode,
        'displayName': unicode,
        Optional('properties'): [_PROPERTY_SCHEMA],
        }],
    required=True,
    extra=True,
    )


def create_property_group(property_group, connection):
    request_body_deserialization = {'name': property_group.name}
    if property_group.display_name:
        request_body_deserialization['displayName'] = \
            property_group.display_name

    response_data = connection.send_put_request(
        '/groups/' + property_group.name,
        request_body_deserialization,
        )
    response_data = _PROPERTY_GROUP_CREATION_SCHEMA(response_data)
    return response_data


def get_all_property_groups(connection):
    response_data = connection.send_get_request('/groups')
    property_groups_data = _PROPERTY_GROUPS_RETRIEVAL_SCHEMA(response_data)
    property_groups = \
        [_build_property_group_from_data(g) for g in property_groups_data]
    return property_groups


def _build_property_group_from_data(property_group_data):
    property_group = PropertyGroup(
        property_group_data['name'],
        property_group_data['displayName'],
        )

    if 'properties' in property_group_data:
        properties_data = property_group_data['properties']
        properties = [_build_property_from_data(p) for p in properties_data]
        property_group.properties = properties

    return property_group
