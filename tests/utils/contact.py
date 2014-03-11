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

from hubspot.contacts import Contact
from six import text_type

from tests.utils.generic import get_random_uuid4_str


def make_contacts(count, **properties):
    contacts = []
    for contact_vid in range(1, count + 1):
        contact = make_contact(contact_vid, **properties)
        contacts.append(contact)
    return contacts


def make_contact(vid, **properties):
    unicode_properties = {
        text_type(k): text_type(v) for k, v in properties.items()
        }

    email_address = _get_random_email_address()
    contact = Contact(vid, email_address, unicode_properties)
    return contact


def _get_random_email_address():
    email_user_name = get_random_uuid4_str()
    email_address = email_user_name + '@example.com'
    return email_address
