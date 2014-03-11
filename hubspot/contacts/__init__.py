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
from six import text_type
from voluptuous import All
from voluptuous import Length
from voluptuous import Schema

from hubspot.contacts._generic_utils import ipaginate
from hubspot.contacts.formatters import format_contacts_data_for_saving
from hubspot.contacts.schema_validators import AnyListItemValidates
from hubspot.contacts.schema_validators import Constant
from hubspot.contacts.schema_validators import DynamicDictionary
from hubspot.contacts.schema_validators import GetDictValue


_HUBSPOT_BATCH_SAVING_SIZE_LIMIT = 1000


Contact = Record.create_type(
    'Contact',
    'vid',
    'email_address',
    'properties',
    )


_CANONICAL_IDENTITY_PROFILE_SCHEMA = {
    'vid': int,
    'identities': All(
        [],
        AnyListItemValidates(
            {'type': Constant(u'EMAIL'), 'value': text_type},
            ),
        ),
    }

_IS_PROPERTY_VALUE = Schema({'value': text_type}, required=True, extra=True)

_GET_ALL_CONTACTS_SCHEMA = Schema(
    {
        'contacts': [{
            'vid': int,
            'properties': DynamicDictionary(
                text_type,
                All(_IS_PROPERTY_VALUE, GetDictValue('value')),
                ),
            'identity-profiles': All(
                [{'vid': int, 'identities': []}],
                Length(min=1),
                AnyListItemValidates(_CANONICAL_IDENTITY_PROFILE_SCHEMA),
                ),
            }],
        'has-more': bool,
        'vid-offset': int,
        },
    required=True,
    extra=True,
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
        contacts_data = _GET_ALL_CONTACTS_SCHEMA(contacts_data)

        for contact_data in contacts_data['contacts']:
            yield contact_data

            last_contact_vid = contact_data['vid']

        has_more_pages = contacts_data['has-more']


def _build_contact_from_data(contact_data):
    email_address = _get_email_address_from_contact_data(contact_data)
    properties = contact_data['properties']
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

    return contact_email_address


def save_contacts(contacts, connection):
    contacts_batches = ipaginate(contacts, _HUBSPOT_BATCH_SAVING_SIZE_LIMIT)
    for contacts_batch in contacts_batches:
        contacts_batch_data = format_contacts_data_for_saving(contacts_batch)
        connection.send_post_request('/contact/batch/', contacts_batch_data)
