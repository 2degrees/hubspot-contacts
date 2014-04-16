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

from hubspot.contacts._data_retrieval import PaginatedDataRetriever
from hubspot.contacts._schemas.lists import CONTACT_LIST_SCHEMA
from hubspot.contacts._schemas.lists import \
    CONTACT_LIST_MEMBERSHIP_UPDATE_SCHEMA


ContactList = Record.create_type(
    'ContactList',
    'id',
    'name',
    'is_dynamic',
    )


def create_static_contact_list(contact_list_name, connection):
    contact_list_data = connection.send_post_request(
        '/lists',
        {'name': contact_list_name, 'dynamic': False},
        )
    contact_list = _build_contact_list_from_data(contact_list_data)
    return contact_list


def get_all_contact_lists(connection):
    data_retriever = PaginatedDataRetriever('lists', ['offset'])
    contact_lists_data = data_retriever.get_data(connection, '/lists')
    contact_lists = _build_contact_lists_from_data(contact_lists_data)
    return contact_lists


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
    if not contacts:
        return []

    contact_vids = [c.vid for c in contacts]
    response_data = connection.send_post_request(
        '/lists/{}/add'.format(contact_list.id),
        {'vids': contact_vids},
        )
    response_data = CONTACT_LIST_MEMBERSHIP_UPDATE_SCHEMA(response_data)

    updated_contact_vids = response_data['updated']
    return updated_contact_vids
