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
from datetime import datetime
from datetime import timedelta
from decimal import Decimal
from json import loads as json_deserialize

from pyrecord import Record

from hubspot.contacts._schemas.contacts import CONTACTS_PAGE_SCHEMA
from hubspot.contacts.generic_utils import ipaginate
from hubspot.contacts.properties import BooleanProperty
from hubspot.contacts.properties import DatetimeProperty
from hubspot.contacts.properties import NumberProperty
from hubspot.contacts.properties import get_all_properties
from hubspot.contacts.request_data_formatters.contacts import \
    format_contacts_data_for_saving


Contact = Record.create_type(
    'Contact',
    'vid',
    'email_address',
    'properties',
    'sub_contacts',
    )


_HUBSPOT_BATCH_SAVING_SIZE_LIMIT = 1000


_HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT = 100


_EPOCH_DATETIME = datetime(1970, 1, 1)


def get_all_contacts(connection, property_names=()):
    all_contacts = _get_contacts_from_all_pages(
        '/lists/all/contacts/all',
        connection,
        property_names,
        )
    return all_contacts


def get_all_contacts_by_last_update(connection, property_names=()):
    all_contacts_by_last_update = _get_contacts_from_all_pages(
        '/lists/recently_updated/contacts/recent',
        connection,
        property_names,
        )
    return all_contacts_by_last_update


def _get_contacts_from_all_pages(path_info, connection, property_names):
    property_type_by_property_name = \
        _get_property_type_by_property_name(connection)

    contacts_data_by_page = \
        _get_contacts_data_by_page(path_info, connection, property_names)
    for contacts_data in contacts_data_by_page:
        for contact_data in contacts_data:
            contact = _build_contact_from_data(
                contact_data,
                property_type_by_property_name,
                )
            yield contact


def _get_contacts_data_by_page(path_info, connection, property_names):
    base_query_string_args = {'count': _HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT}
    if property_names:
        base_query_string_args['property'] = property_names
    has_more_pages = True
    last_contact_vid = None
    last_contact_addition_timestamp = None
    while has_more_pages:
        query_string_args = base_query_string_args.copy()
        if last_contact_vid:
            query_string_args['vidOffset'] = last_contact_vid
        if last_contact_addition_timestamp:
            query_string_args['timeOffset'] = last_contact_addition_timestamp

        contacts_data = \
            connection.send_get_request(path_info, query_string_args)
        contacts_data = CONTACTS_PAGE_SCHEMA(contacts_data)

        yield contacts_data['contacts']

        last_contact_vid = contacts_data['vid-offset']
        last_contact_addition_timestamp = contacts_data.get('time-offset')
        has_more_pages = contacts_data['has-more']


def _convert_timestamp_in_milliseconds_to_datetime(timestamp_milliseconds):
    timestamp_milliseconds = int(timestamp_milliseconds)
    time_since_epoch = timedelta(milliseconds=timestamp_milliseconds)
    timestamp_as_datetime = _EPOCH_DATETIME + time_since_epoch
    return timestamp_as_datetime


_PROPERTY_VALUE_CONVERTER_BY_PROPERTY_TYPE = defaultdict(
    lambda: unicode,
    {
        BooleanProperty: json_deserialize,
        DatetimeProperty: _convert_timestamp_in_milliseconds_to_datetime,
        NumberProperty: Decimal,
        },
    )


def _build_contact_from_data(contact_data, property_type_by_property_name):
    canonical_profile_data, additional_profiles_data = \
        _get_profiles_data_from_contact_data(contact_data)
    email_address = \
        _get_email_address_from_contact_profile_data(canonical_profile_data)
    sub_contacts = _get_sub_contacts_from_contact_data(additional_profiles_data)

    properties = {}
    for property_name, property_value in contact_data['properties'].items():
        property_type = property_type_by_property_name.get(property_name)
        if property_type:
            converter = \
                _PROPERTY_VALUE_CONVERTER_BY_PROPERTY_TYPE[property_type]
            properties[property_name] = converter(property_value)

    return Contact(contact_data['vid'], email_address, properties, sub_contacts)


def _get_profiles_data_from_contact_data(contact_data):
    additional_profiles_data = []
    for related_contact_profile_data in contact_data['identity-profiles']:
        if related_contact_profile_data['vid'] == contact_data['vid']:
            canonical_profile_data = related_contact_profile_data
        else:
            additional_profiles_data.append(related_contact_profile_data)

    return canonical_profile_data, additional_profiles_data


def _get_sub_contacts_from_contact_data(contact_profiles_data):
    sub_contacts = [profile['vid'] for profile in contact_profiles_data]
    return sub_contacts


def _get_email_address_from_contact_profile_data(contact_profile_data):
    contact_email_address = None
    for identity in contact_profile_data['identities']:
        if identity['type'] == 'EMAIL':
            contact_email_address = identity['value']
            break
    return contact_email_address


def save_contacts(contacts, connection):
    property_type_by_property_name = \
        _get_property_type_by_property_name(connection)

    contacts_batches = ipaginate(contacts, _HUBSPOT_BATCH_SAVING_SIZE_LIMIT)
    for contacts_batch in contacts_batches:
        contacts_batch_data = format_contacts_data_for_saving(
            contacts_batch,
            property_type_by_property_name,
            )
        connection.send_post_request('/contact/batch/', contacts_batch_data)


def _get_property_type_by_property_name(connection):
    property_definitions = get_all_properties(connection)
    property_type_by_property_name = \
        {p.name: type(p) for p in property_definitions}
    return property_type_by_property_name
