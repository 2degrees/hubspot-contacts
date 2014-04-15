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


ContactList = Record.create_type(
    'ContactList',
    'id',
    'name',
    'is_dynamic',
    )


def get_all_contact_lists(connection):
    data_retriever = PaginatedDataRetriever('lists', ['offset'])
    contact_lists_data = data_retriever.get_data(
        connection,
        '/contacts/v1/lists',
        )
    contact_lists = _build_contact_lists_from_data(contact_lists_data)
    return contact_lists


def _build_contact_lists_from_data(contact_lists_data):
    for contact_list_data in contact_lists_data:
        contact_list = ContactList(
            contact_list_data['listId'],
            contact_list_data['name'],
            contact_list_data['dynamic'],
            )
        yield contact_list
