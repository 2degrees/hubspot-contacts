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
"""
Test utilities.

These are not unit tested because they're considered part of the test suite,
so doing so would mean testing the tests.

"""

from datetime import datetime
from json import dumps as json_serialize

from hubspot.connection.testing import ConstantResponseDataMaker
from hubspot.connection.testing import NULL_RESPONSE_DATA_MAKER

from hubspot.contacts._batching_limits import HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT
from hubspot.contacts.generic_utils import \
    convert_date_to_timestamp_in_milliseconds
from hubspot.contacts.generic_utils import get_uuid4_str
from hubspot.contacts.generic_utils import paginate
from hubspot.contacts.request_data_formatters.properties import \
    format_data_for_property


_STUB_TIMESTAMP = 12345


class AllContactsRetrievalResponseDataMaker(object):

    def __init__(self, contacts):
        super(AllContactsRetrievalResponseDataMaker, self).__init__()

        self._contacts_by_page = \
            paginate(contacts, HUBSPOT_BATCH_RETRIEVAL_SIZE_LIMIT)
        self._requests_made_count = 0

    def __call__(self, query_string_args, body_deserialization):
        required_property_names = query_string_args.get('property', [])
        self._requests_made_count += 1
        response_data = _format_data_from_all_contacts_retrieval(
            self._contacts_by_page,
            self._requests_made_count,
            required_property_names,
            )
        return response_data


def _format_data_from_all_contacts_retrieval(
    contacts_by_page,
    page_number,
    required_property_names,
    ):
    page_contacts = \
        contacts_by_page[page_number - 1] if contacts_by_page else []
    pages_count = len(contacts_by_page)
    page_has_successors = page_number < pages_count

    page_last_contact = page_contacts[-1] if page_contacts else None
    page_last_contact_vid = page_last_contact.vid if page_last_contact else 0

    page_contacts_data = _format_contacts_as_data_from_all_contacts_retrieval(
        page_contacts,
        required_property_names,
        )

    return {
        'contacts': page_contacts_data,
        'has-more': page_has_successors,
        'vid-offset': page_last_contact_vid,
        }


def _format_contacts_as_data_from_all_contacts_retrieval(
    all_contacts,
    required_property_names,
    ):
    contacts_data = []
    for contact in all_contacts:
        contact_data = {
            'vid': contact.vid,
            'canonical-vid': contact.vid,
            'properties': _format_contact_properties_data(
                contact.properties,
                required_property_names,
                ),
            'identity-profiles': _format_contact_profiles_data(contact),
            }
        contacts_data.append(contact_data)

    return contacts_data


def _format_contact_properties_data(
    contact_properties,
    required_property_names,
    ):
    contact_properties_data = {}
    for property_name in required_property_names:
        if property_name not in contact_properties:
            continue

        property_value = contact_properties[property_name]

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

    for vid in contact.related_contact_vids:
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


class RecentlyUpdatedContactsRetrievalResponseDataMaker(
    AllContactsRetrievalResponseDataMaker,
    ):

    def __call__(self, query_string_args, body_deserialization):
        super_ = super(RecentlyUpdatedContactsRetrievalResponseDataMaker, self)
        response_data = super_.__call__(query_string_args, body_deserialization)

        time_offset = query_string_args.get('timeOffset', _STUB_TIMESTAMP)

        contacts_data = response_data['contacts']
        for contact_index, contact_data in enumerate(contacts_data, 1):
            contact_data['addedAt'] = time_offset - contact_index

        response_data['time-offset'] = time_offset - len(contacts_data)
        return response_data


CONTACT_SAVING_RESPONSE_DATA_MAKER = NULL_RESPONSE_DATA_MAKER


class AllPropertiesRetrievalResponseDataMaker(ConstantResponseDataMaker):

    def __init__(self, properties):
        properties_data = _format_data_for_properties(properties)

        super_ = super(AllPropertiesRetrievalResponseDataMaker, self)
        super_.__init__(properties_data)


class PropertyCreationRetrievalResponseDataMaker(ConstantResponseDataMaker):

    def __init__(self, property_):
        property_data = format_data_for_property(property_)

        super_ = super(PropertyCreationRetrievalResponseDataMaker, self)
        super_.__init__(property_data)


class AllPropertyGroupsRetrievalResponseDataMaker(ConstantResponseDataMaker):

    def __init__(self, property_groups):
        property_groups_data = \
            [_format_data_for_property_group(g) for g in property_groups]

        super_ = super(AllPropertyGroupsRetrievalResponseDataMaker, self)
        super_.__init__(property_groups_data)


class PropertyGroupCreationResponseDataMaker(ConstantResponseDataMaker):

    def __init__(self, property_group):
        property_group_data = _format_data_for_property_group(property_group)

        super_ = super(PropertyGroupCreationResponseDataMaker, self)
        super_.__init__(property_group_data)


def _format_data_for_property_group(property_group):
    property_group_data = {
        'name': property_group.name,
        'displayName': property_group.display_name or '',
        'displayOrder': 1,
        'portalId': 1,
        }
    if property_group.properties:
        property_group_data['properties'] = \
            _format_data_for_properties(property_group.properties)
    return property_group_data


def _format_data_for_properties(properties):
    properties_data = [format_data_for_property(p) for p in properties]
    return properties_data


PROPERTY_DELETION_RESPONSE_DATA_MAKER = NULL_RESPONSE_DATA_MAKER
