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
from hubspot.contacts._constants import BATCH_SAVING_SIZE_LIMIT
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
from hubspot.contacts.generic_utils import ipaginate
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
    """
    Create a static contact list named ``contact_list_name``.
    
    :param basestring contact_list_name:
    :return ContactList: The resulting list as created by HubSpot
    :raises hubspot.connection.exc.HubspotException:
    
    """
    contact_list_data = connection.send_post_request(
        _CONTACT_LIST_COLLECTION_URL_PATH,
        {'name': contact_list_name, 'dynamic': False},
        )
    contact_list = _build_contact_list_from_data(contact_list_data)
    return contact_list


def get_all_contact_lists(connection):
    """
    Get the meta-information for all the contact lists in the portal.
    
    :return: An iterator with :class:`ContactList` instances
    :raises hubspot.connection.exc.HubspotException:
    
    This function is a generator and requests are sent on demand. This is, the
    first request to HubSpot is deferred until the first list in the result
    is used, and from there on subsequent requests may be sent as the iterator
    is consumed.
    
    End-point documentation:
    http://developers.hubspot.com/docs/methods/lists/get_lists
    
    """
    data_retriever = PaginatedDataRetriever('lists', ['offset'])
    contact_lists_data = \
        data_retriever.get_data(connection, _CONTACT_LIST_COLLECTION_URL_PATH)
    contact_lists = _build_contact_lists_from_data(contact_lists_data)
    return contact_lists


def delete_contact_list(contact_list_id, connection):
    """
    Delete the contact list identified by ``contact_list_id``.
    
    :param int contact_list_id: The identifier of the contact list to be removed
    :return: ``None``
    :raises hubspot.connection.exc.HubspotException:
    
    End-point documentation:
    http://developers.hubspot.com/docs/methods/lists/delete_list
    
    """
    contact_list_id = int(contact_list_id)
    url_path = \
        '{}/{}'.format(_CONTACT_LIST_COLLECTION_URL_PATH, contact_list_id)
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
    """
    Add ``contacts`` to ``contact_list``.
    
    :param ContactList contact_list: The list to which ``contacts`` must be
        added
    :param iterator contacts: The contacts to add to ``contact_list``
    :return: The VIDs corresponding to the contacts that were successfully
        added to the list
    :raises hubspot.connection.exc.HubspotException:
    
    End-point documentation:
    http://developers.hubspot.com/docs/methods/lists/add_contact_to_list
    
    """
    path_info = '/lists/{}/add'.format(contact_list.id)
    updated_contact_vids = _update_contact_list_membership(
        CONTACTS_API_SCRIPT_NAME + path_info,
        contacts,
        connection,
        )
    return updated_contact_vids


def remove_contacts_from_list(contact_list, contacts, connection):
    """
    Remove ``contacts`` from ``contact_list``.
    
    :param ContactList contact_list: The list from which ``contacts`` must be
        removed
    :param iterator contacts: The contacts to remove from ``contact_list``
    :return: The VIDs corresponding to the contacts that were successfully
        removed from the list
    :raises hubspot.connection.exc.HubspotException:
    
    End-point documentation:
    http://developers.hubspot.com/docs/methods/lists/remove_contact_from_list
    
    """
    path_info = '/lists/{}/remove'.format(contact_list.id)
    updated_contact_vids = _update_contact_list_membership(
        CONTACTS_API_SCRIPT_NAME + path_info,
        contacts,
        connection,
        )
    return updated_contact_vids


def _update_contact_list_membership(endpoint_url_path, contacts, connection):
    updated_contact_vids = []

    contacts_batches = ipaginate(contacts, BATCH_SAVING_SIZE_LIMIT)
    for contacts_batch in contacts_batches:
        contact_vids = [c.vid for c in contacts_batch]
        response_data = connection.send_post_request(
            endpoint_url_path,
            {'vids': contact_vids},
            )
        response_data = CONTACT_LIST_MEMBERSHIP_UPDATE_SCHEMA(response_data)

        updated_contact_vids.extend(response_data['updated'])

    return updated_contact_vids


def get_all_contacts(connection, property_names=()):
    """
    Get all the contacts in the portal.
    
    :param property_names: The names of the properties to be retrieved for each
        contact
    :return: An iterator with :class:`Contact` instances
    :raises hubspot.connection.exc.HubspotException:
    
    If ``property_names`` is empty, no specific properties are requested to
    HubSpot. Otherwise, values are passed as is to HubSpot.
    
    This function is a generator and requests are sent on demand. This is, the
    first request to HubSpot is deferred until the first contact in the result
    is used, and from there on subsequent requests may be sent as the iterator
    is consumed.
    
    Generally speaking, the contacts returned, their order and their properties
    are determined by HubSpot, with the following exceptions:
    
    - Property values in each contact are type-cast to an appropriate, built-in
      datatype.
    - Duplicated contacts (i.e., multiple contacts with the same *VID*) are
      discarded.
    
    End-point documentation:
    http://developers.hubspot.com/docs/methods/contacts/get_contacts
    
    """
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
    """
    Get all the contacts in the portal, starting with the most recently updated
    ones.
    
    :param property_names: The names of the properties to be retrieved for each
        contact
    :param datetime.datetime cutoff_datetime: The minimum datetime for the last
        update to any contact returned
    :return: An iterator with :class:`Contact` instances
    :raises hubspot.connection.exc.HubspotException:
    
    If ``cutoff_datetime`` is set, only contacts that were last updated at that
    time or later are returned. If unset, all the contacts are returned and
    sorted by their last update (most recent first).
    
    Apart from the special considerations given to the contacts' last update
    date, this behaves exactly like :func:`get_all_contacts`. But because this
    uses a different HubSpot API end-point, the output may be slightly
    different; for instance, as at this writing, one known difference is that
    this end-point also returns contacts for whom there are no registered email
    addresses.
    
    End-point documentation:
    http://developers.hubspot.com/docs/methods/contacts/get_recently_updated_contacts
    
    """
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
    """
    Get all the contacts in ``contact_list``, starting with the most recently
    added ones.
    
    :param ContactList contact_list: The list whose contacts should be retrieved
    :param property_names: The names of the properties to be retrieved for each
        contact
    :return: An iterator with :class:`Contact` instances
    :raises hubspot.connection.exc.HubspotException:
    
    If ``cutoff_datetime`` is set, only contacts that were added at that time or
    later are returned. If unset, all the contacts in the list are returned and
    sorted by the time they were added (most recent first).
    
    Apart from the special considerations given to the time the contact was
    added to the list, this function behaves exactly like
    :func:`get_all_contacts_from_list`. But because this uses a different
    HubSpot API end-point, the output may be slightly different.
    
    End-point documentation:
    http://developers.hubspot.com/docs/methods/lists/get_list_contacts_recent
    
    """
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
    """
    Get all the contacts in ``contact_list``.
    
    :param ContactList contact_list: The list whose contacts should be retrieved
    :param property_names: The names of the properties to be retrieved for each
        contact
    :return: An iterator with :class:`Contact` instances
    :raises hubspot.connection.exc.HubspotException:
    
    Other than the contacts being limited to ``contact_list``, this function
    behaves exactly like :func:`get_all_contacts`. But because this uses a
    different HubSpot API end-point, the output may be slightly different.
    
    End-point documentation:
    http://developers.hubspot.com/docs/methods/lists/get_list_contacts
    
    """
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
