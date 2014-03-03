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

from hubspot.contacts._generic_utils import ipaginate
from hubspot.contacts.formatters import format_contacts_data_for_saving


_HUBSPOT_BATCH_SAVING_SIZE_LIMIT = 1000


Contact = Record.create_type(
    'Contact',
    'vid',
    'email_address',
    'properties',
    )


def get_all_contacts(connection, page_size=None, properties=()):
    all_contacts_data = \
        _get_all_contacts_data(connection, page_size, properties)
    for contact_data in all_contacts_data:
        contact = _build_contact_from_data(contact_data)
        yield contact


def _get_all_contacts_data(connection, page_size, properties):
    base_query_string_args = {}
    if page_size:
        base_query_string_args['count'] = page_size
    if properties:
        base_query_string_args['property'] = properties

    has_more_pages = True
    last_contact_vid = None
    while has_more_pages:
        query_string_args = base_query_string_args.copy()
        if last_contact_vid:
            query_string_args['vidOffset'] = last_contact_vid

        contacts_data = connection.send_get_request(
            '/lists/all/contacts/all',
            query_string_args,
            )

        for contact_data in contacts_data['contacts']:
            yield contact_data

            last_contact_vid = contact_data['vid']

        has_more_pages = contacts_data['has-more']


def _build_contact_from_data(contact_data):
    email_address = _get_email_address_from_contact_data(contact_data)
    properties = _get_property_items_flattened(contact_data['properties'])
    return Contact(contact_data['vid'], email_address, properties)


def _get_email_address_from_contact_data(contact_data):
    contact_profile_data = _get_profile_data_from_contact_data(contact_data)
    contact_email_address = \
        _get_email_address_from_contact_profile_data(contact_profile_data)
    return contact_email_address


def _get_profile_data_from_contact_data(contact_data):
    contact_profile_data = None
    for related_contact_profile_data in contact_data['identity-profiles']:
        if related_contact_profile_data['vid'] == contact_data['vid']:
            contact_profile_data = related_contact_profile_data
            break

    assert contact_profile_data
    return contact_profile_data


def _get_email_address_from_contact_profile_data(contact_profile_data):
    contact_email_address = None
    for identity in contact_profile_data['identities']:
        if identity['type'] == 'EMAIL':
            contact_email_address = identity['value']
            break

    assert contact_email_address
    return contact_email_address


def _get_property_items_flattened(contact_properties_data):
    contact_properties = \
        {key: data['value'] for key, data in contact_properties_data.items()}
    return contact_properties


def save_contacts(contacts, connection):
    contacts_batches = ipaginate(contacts, _HUBSPOT_BATCH_SAVING_SIZE_LIMIT)
    for contacts_batch in contacts_batches:
        contacts_batch_data = format_contacts_data_for_saving(contacts_batch)
        connection.send_post_request('/contact/batch/', contacts_batch_data)
