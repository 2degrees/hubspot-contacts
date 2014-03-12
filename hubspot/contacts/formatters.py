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


def format_contacts_data_for_saving(contacts):
    contacts_data = [_format_contact_data_for_saving(c) for c in contacts]
    return contacts_data


def _format_contact_data_for_saving(contact):
    contact_data = {
        'email': contact.email_address,
        'properties': _format_contact_properties_for_saving(contact.properties),
        }
    return contact_data


def _format_contact_properties_for_saving(contact_properties):
    contact_properties_data = [
        {'property': n, 'value': v} for n, v in contact_properties.items()
        ]
    return contact_properties_data
