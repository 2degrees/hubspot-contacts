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

from datetime import datetime
from json import dumps as json_serialize

from hubspot.contacts.generic_utils import \
    convert_date_to_timestamp_in_milliseconds

from tests.utils.generic import get_uuid4_str


STUB_TIMESTAMP = 12345


def format_data_from_all_contacts_retrieval(
    page_contacts,
    all_contacts,
    page_size,
    ):
    page_number = _get_current_contacts_page_number(
        page_contacts,
        all_contacts,
        page_size,
        )

    pages_count = _get_contact_pages_count(all_contacts, page_size)
    page_has_successors = page_number < pages_count

    page_last_contact = page_contacts[-1] if page_contacts else None
    page_last_contact_vid = page_last_contact.vid if page_last_contact else 0

    page_contacts_data = \
        _format_contacts_as_data_from_all_contacts_retrieval(page_contacts)

    return {
        'contacts': page_contacts_data,
        'has-more': page_has_successors,
        'vid-offset': page_last_contact_vid,
        }


def format_data_from_all_contacts_by_last_update_retrieval(
    page_contacts,
    all_contacts,
    page_size,
    ):
    retrieval_data = format_data_from_all_contacts_retrieval(
        page_contacts,
        all_contacts,
        page_size,
        )
    retrieval_data['time-offset'] = STUB_TIMESTAMP
    return retrieval_data


def _format_contacts_as_data_from_all_contacts_retrieval(all_contacts):
    contacts_data = []
    for contact in all_contacts:
        contact_data = {
            'vid': contact.vid,
            'canonical-vid': contact.vid,
            'properties': _format_contact_properties_data(contact.properties),
            'identity-profiles': _format_contact_profiles_data(contact),
            }
        contacts_data.append(contact_data)

    return contacts_data


def _format_contact_properties_data(contact_properties):
    contact_properties_data = {}
    for property_name, property_value in contact_properties.items():
        if isinstance(property_value, bool):
            property_value = json_serialize(property_value)
        elif isinstance(property_value, datetime):
            property_value = \
                convert_date_to_timestamp_in_milliseconds(property_value)

        property_value = unicode(property_value)
        contact_properties_data[property_name] = {
            'value': property_value,
            'versions': [],
            }
    return contact_properties_data


def _format_contact_profiles_data(contact):
    contact_profile_data = {
        'vid': contact.vid,
        'identities': [
            {'type': u'LEAD_GUID', 'value': get_uuid4_str()},
            {'type': u'EMAIL', 'value': contact.email_address},
            ],
        }
    contact_profiles_data = [contact_profile_data]

    for vid in contact.sub_contacts:
        contact_profiles_data.append({'vid': vid, 'identities': []})

    return contact_profiles_data


def _get_contact_pages_count(all_contacts, page_size):
    if all_contacts:
        contacts_count = len(all_contacts)
        last_contact_index = contacts_count - 1
        contact_pages_count = (last_contact_index // page_size) + 1
    else:
        contact_pages_count = 1
    return contact_pages_count


def _get_current_contacts_page_number(page_contacts, all_contacts, page_size):
    if all_contacts:
        page_first_contact = page_contacts[0]
        page_first_contact_index = all_contacts.index(page_first_contact)
        page_number = (page_first_contact_index // page_size) + 1
    else:
        page_number = 1
    return page_number
