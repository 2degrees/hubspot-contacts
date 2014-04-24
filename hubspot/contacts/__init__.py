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

from hubspot.contacts._constants import BATCH_SAVING_SIZE_LIMIT
from hubspot.contacts._constants import CONTACTS_API_SCRIPT_NAME
from hubspot.contacts._property_utils import get_property_type_by_property_name
from hubspot.contacts.generic_utils import ipaginate
from hubspot.contacts.request_data_formatters.contacts import \
    format_contacts_data_for_saving


Contact = Record.create_type(
    'Contact',
    'vid',
    'email_address',
    'properties',
    'related_contact_vids',
    )


_CONTACTS_SAVING_URL_PATH = CONTACTS_API_SCRIPT_NAME + '/contact/batch/'


def save_contacts(contacts, connection):
    property_type_by_property_name = \
        get_property_type_by_property_name(connection)

    contacts_batches = ipaginate(contacts, BATCH_SAVING_SIZE_LIMIT)
    for contacts_batch in contacts_batches:
        contacts_batch_data = format_contacts_data_for_saving(
            contacts_batch,
            property_type_by_property_name,
            )
        connection.send_post_request(
            _CONTACTS_SAVING_URL_PATH,
            contacts_batch_data,
            )
