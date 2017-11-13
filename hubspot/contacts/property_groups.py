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

from hubspot.contacts._constants import CONTACTS_API_SCRIPT_NAME
from hubspot.contacts._schemas.properties import \
    PROPERTY_RESPONSE_SCHEMA_DEFINITION
from hubspot.contacts.properties import _build_property_from_data
from hubspot.contacts.request_data_formatters.property_groups import \
    format_data_for_property_group

PropertyGroup = Record.create_type(
    'PropertyGroup',
    'name',
    'display_name',
    'properties',
    display_name=None,
    properties=(),
)

_PROPERTY_GROUP_CREATION_SCHEMA = Schema(
    {'name': unicode, 'displayName': unicode},
    required=True,
    extra=True,
)

_PROPERTY_GROUPS_RETRIEVAL_SCHEMA = Schema(
    [{
        'name': unicode,
        'displayName': unicode,
        Optional('properties'): [PROPERTY_RESPONSE_SCHEMA_DEFINITION],
    }],
    required=True,
    extra=True,
)

_PROPERTY_GROUPS_RETRIEVAL_URL_PATH = CONTACTS_API_SCRIPT_NAME + '/groups'


def get_all_property_groups(connection):
    """
    Get the meta-information for all the property groups in the portal.
    
    :rtype: :class:`list` of :class:`PropertyGroup` instances
    :raises hubspot.connection.exc.HubspotException:
    
    End-point documentation:
    http://developers.hubspot.com/docs/methods/contacts/get_groups
    
    """
    response_data = \
        connection.send_get_request(_PROPERTY_GROUPS_RETRIEVAL_URL_PATH)
    property_groups_data = _PROPERTY_GROUPS_RETRIEVAL_SCHEMA(response_data)
    property_groups = \
        [_build_property_group_from_data(g) for g in property_groups_data]
    return property_groups


def create_property_group(property_group, connection):
    """
    Create ``property_group``.
    
    :param Property property_: The property group to be created
    :return: :class:`PropertyGroup` instance as created by HubSpot
    :raises hubspot.connection.exc.HubspotException:
    
    End-point documentation:
    http://developers.hubspot.com/docs/methods/contacts/create_group
    
    """
    request_body_deserialization = \
        format_data_for_property_group(property_group)

    url_path = CONTACTS_API_SCRIPT_NAME + '/groups/' + property_group.name
    response_data = connection.send_put_request(
        url_path,
        request_body_deserialization,
    )
    property_group_data = _PROPERTY_GROUP_CREATION_SCHEMA(response_data)
    created_property_group = \
        _build_property_group_from_data(property_group_data)
    return created_property_group


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


def delete_property_group(property_group_name, connection):
    """
    Delete the property group named ``property_group_name``.
    
    :param PropertyGroup property_group_name: The name of the property group to
        be deleted
    :return: ``None``
    :raises hubspot.connection.exc.HubspotException:
    
    End-point documentation:
    http://developers.hubspot.com/docs/methods/contacts/delete_group
    
    """
    url_path = CONTACTS_API_SCRIPT_NAME + '/groups/' + property_group_name
    connection.send_delete_request(url_path)
