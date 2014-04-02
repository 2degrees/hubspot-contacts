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


# TODO: Move to sub-module
def format_data_for_property(property_):
    property_type = _get_property_type_name(property_)
    property_options = _get_raw_property_options(property_)
    property_data = {
        'name': property_.name,
        'label': property_.label,
        'description': property_.description,
        'groupName': property_.group_name,
        'fieldType': property_.field_widget,
        'type': property_type,
        'options': property_options,
        }
    return property_data


def _get_property_type_name(property_):
    # Move to module-level, avoiding cyclic import
    from hubspot.contacts.properties import PROPERTY_TYPE_BY_NAME
    _PROPERTY_TYPE_NAME_BY_PROPERTY_TYPE = \
        {type_: type_name  for type_name, type_ in PROPERTY_TYPE_BY_NAME.items()}

    property_type = property_.__class__
    property_type_name = _PROPERTY_TYPE_NAME_BY_PROPERTY_TYPE[property_type]
    return property_type_name


def _get_raw_property_options(property_):
    from hubspot.contacts.properties import BooleanProperty
    from hubspot.contacts.properties import EnumerationProperty

    if isinstance(property_, BooleanProperty):
        raw_options_data = [
            {'label': 'True', 'value': 'true', 'displayOrder': 0},
            {'label': 'False', 'value': 'false', 'displayOrder': 1},
            ]
    elif isinstance(property_, EnumerationProperty):
        raw_options_data = []
        for option_label, option_value in property_.options.items():
            option_data = {
                'label': option_label,
                'value': option_value,
                'displayOrder': 0,
                }
            raw_options_data.append(option_data)
    else:
        raw_options_data = []

    return raw_options_data
