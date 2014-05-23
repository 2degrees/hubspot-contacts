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

from collections import defaultdict
from decimal import Decimal
from json import loads as json_deserialize

from pyrecord import Record

from hubspot.contacts import Contact
from hubspot.contacts._constants import CONTACTS_API_SCRIPT_NAME
from hubspot.contacts._data_retrieval import PaginatedDataRetriever
from hubspot.contacts._property_utils import get_property_type_by_property_name
from hubspot.contacts._schemas.contacts import CONTACT_SCHEMA
from hubspot.contacts._schemas.lists import \
    CONTACT_LIST_MEMBERSHIP_UPDATE_SCHEMA
from hubspot.contacts._schemas.lists import CONTACT_LIST_SCHEMA
from hubspot.contacts.generic_utils import \
    convert_date_to_timestamp_in_milliseconds
from hubspot.contacts.generic_utils import \
    convert_timestamp_in_milliseconds_to_date
from hubspot.contacts.generic_utils import \
    convert_timestamp_in_milliseconds_to_datetime
from hubspot.contacts.properties import BooleanProperty
from hubspot.contacts.properties import DateProperty
from hubspot.contacts.properties import DatetimeProperty
from hubspot.contacts.properties import NumberProperty


_CONTACT_LIST_COLLECTION_URL_PATH = CONTACTS_API_SCRIPT_NAME + '/lists'


_PROPERTY_VALUE_CONVERTER_BY_PROPERTY_TYPE = defaultdict(
    lambda: unicode,
    {
        BooleanProperty: json_deserialize,
        DateProperty: convert_timestamp_in_milliseconds_to_date,
        DatetimeProperty: convert_timestamp_in_milliseconds_to_datetime,
        NumberProperty: Decimal,
        },
    )


ContactList = Record.create_type(
    'ContactList',
    'id',
    'name',
    'is_dynamic',
    )


def create_static_contact_list(contact_list_name, connection):
    contact_list_data = connection.send_post_request(
        _CONTACT_LIST_COLLECTION_URL_PATH,
        {'name': contact_list_name, 'dynamic': False},
        )
    contact_list = _build_contact_list_from_data(contact_list_data)
    return contact_list


def get_all_contact_lists(connection):
    data_retriever = PaginatedDataRetriever('lists', ['offset'])
    contact_lists_data = \
        data_retriever.get_data(connection, _CONTACT_LIST_COLLECTION_URL_PATH)
    contact_lists = _build_contact_lists_from_data(contact_lists_data)
    return contact_lists


def delete_contact_list(contacts_list_id, connection):
    contacts_list_id = int(contacts_list_id)
    url_path = \
        '{}/{}'.format(_CONTACT_LIST_COLLECTION_URL_PATH, contacts_list_id)
    connection.send_delete_request(url_path)


def _build_contact_lists_from_data(contact_lists_data):
    for contact_list_data in contact_lists_data:
        contact_list = _build_contact_list_from_data(contact_list_data)
        yield contact_list


def _build_contact_list_from_data(contact_list_data):
    contact_list_data = CONTACT_LIST_SCHEMA(contact_list_data)
    contact_list = ContactList(
        contact_list_data['listId'],
        contact_list_data['name'],
        contact_list_data['dynamic'],
        )
    return contact_list


def add_contacts_to_list(contact_list, contacts, connection):
    path_info = '/lists/{}/add'.format(contact_list.id)
    updated_contact_vids = _update_contact_list_membership(
        CONTACTS_API_SCRIPT_NAME + path_info,
        contacts,
        connection,
        )
    return updated_contact_vids


def remove_contacts_from_list(contact_list, contacts, connection):
    path_info = '/lists/{}/remove'.format(contact_list.id)
    updated_contact_vids = _update_contact_list_membership(
        CONTACTS_API_SCRIPT_NAME + path_info,
        contacts,
        connection,
        )
    return updated_contact_vids


def _update_contact_list_membership(endpoint_url_path, contacts, connection):
    if not contacts:
        return []

    contact_vids = [c.vid for c in contacts]
    response_data = connection.send_post_request(
        endpoint_url_path,
        {'vids': contact_vids},
        )
    response_data = CONTACT_LIST_MEMBERSHIP_UPDATE_SCHEMA(response_data)

    updated_contact_vids = response_data['updated']
    return updated_contact_vids


def get_all_contacts(connection, property_names=()):
    all_contacts = _get_contacts_from_all_pages(
        '/lists/all/contacts/all',
        connection,
        property_names,
        )
    return all_contacts


def get_all_contacts_by_last_update(
    connection,
    property_names=(),
    cutoff_datetime=None,
    ):
    return _get_contacts_from_all_pages_by_recency(
        'recently_updated',
        connection,
        property_names,
        cutoff_datetime,
        )


def get_all_contacts_from_list_by_added_date(
    contact_list,
    connection,
    property_names=(),
    cutoff_datetime=None,
    ):
    return _get_contacts_from_all_pages_by_recency(
        contact_list.id,
        connection,
        property_names,
        cutoff_datetime,
        )


def _get_contacts_from_all_pages_by_recency(
    contact_list_id,
    connection,
    property_names=(),
    cutoff_datetime=None,
    ):
    contacts_data = _get_contacts_data(
        connection,
        '/lists/{}/contacts/recent'.format(contact_list_id),
        ('vid-offset', 'time-offset'),
        property_names,
        )

    if cutoff_datetime:
        cutoff_timestamp = \
            convert_date_to_timestamp_in_milliseconds(cutoff_datetime)
    else:
        cutoff_timestamp = None

    property_type_by_property_name = \
        get_property_type_by_property_name(connection)

    seen_contact_vids = set()
    for contact_data in contacts_data:
        contact = _build_contact_from_data(
            contact_data,
            property_type_by_property_name,
            )

        if contact.vid in seen_contact_vids:
            continue

        seen_contact_vids.add(contact.vid)

        if cutoff_timestamp and contact_data['addedAt'] < cutoff_timestamp:
            raise StopIteration()

        yield contact


def get_all_contacts_from_list(connection, contact_list, property_names=()):
    contacts_from_list = _get_contacts_from_all_pages(
        '/lists/{}/contacts/all'.format(contact_list.id),
        connection,
        property_names,
        )
    return contacts_from_list


def _get_contacts_from_all_pages(path_info, connection, property_names):
    property_type_by_property_name = \
        get_property_type_by_property_name(connection)

    contacts_data = _get_contacts_data(
        connection,
        path_info,
        ['vid-offset'],
        property_names,
        )

    contacts = \
        _build_contacts_from_data(contacts_data, property_type_by_property_name)
    return contacts


def _get_contacts_data(connection, path_info, pagination_keys, property_names):
    if property_names:
        query_string_args = {'property': property_names}
    else:
        query_string_args = None

    data_retriever = PaginatedDataRetriever('contacts', pagination_keys)
    url_path = CONTACTS_API_SCRIPT_NAME + path_info
    contacts_data = \
        data_retriever.get_data(connection, url_path, query_string_args)
    return contacts_data


def _build_contacts_from_data(contacts_data, property_type_by_property_name):
    for contact_data in contacts_data:
        contact = _build_contact_from_data(
            contact_data,
            property_type_by_property_name,
            )

        yield contact


def _build_contact_from_data(contact_data, property_type_by_property_name):
    contact_data = CONTACT_SCHEMA(contact_data)

    canonical_profile_data, related_profiles_data = \
        _get_profiles_data_from_contact_data(contact_data)
    email_address = \
        _get_email_address_from_contact_profile_data(canonical_profile_data)
    related_contact_vids = \
        _get_contact_vids_from_contact_profiles_data(related_profiles_data)

    properties = {}
    for property_name, property_value in contact_data['properties'].items():
        property_type = property_type_by_property_name.get(property_name)
        if property_type and property_value:
            converter = \
                _PROPERTY_VALUE_CONVERTER_BY_PROPERTY_TYPE[property_type]
            properties[property_name] = converter(property_value)

    contact = Contact(
        contact_data['vid'],
        email_address,
        properties,
        related_contact_vids,
        )
    return contact


def _get_profiles_data_from_contact_data(contact_data):
    related_profiles_data = []
    for related_contact_profile_data in contact_data['identity-profiles']:
        if related_contact_profile_data['vid'] == contact_data['vid']:
            canonical_profile_data = related_contact_profile_data
        else:
            related_profiles_data.append(related_contact_profile_data)

    return canonical_profile_data, related_profiles_data


def _get_contact_vids_from_contact_profiles_data(contact_profiles_data):
    contact_vids = [profile['vid'] for profile in contact_profiles_data]
    return contact_vids


def _get_email_address_from_contact_profile_data(contact_profile_data):
    contact_email_address = None
    for identity in contact_profile_data['identities']:
        if identity['type'] == 'EMAIL':
            contact_email_address = identity['value']
            break
    return contact_email_address
