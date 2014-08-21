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

from hubspot.contacts.properties import BooleanProperty
from hubspot.contacts.properties import PROPERTY_TYPE_BY_NAME


def format_data_for_property(property_):
    property_type = _get_property_type_name(property_)
    property_options = _get_raw_property_options(property_)

    if isinstance(property_, BooleanProperty) and not property_.field_widget:
        field_widget = 'booleancheckbox'
    else:
        field_widget = property_.field_widget

    property_data = {
        'name': property_.name,
        'label': property_.label,
        'description': property_.description,
        'groupName': property_.group_name,
        'fieldType': field_widget,
        'type': property_type,
        'options': property_options,
        }
    return property_data


def _get_property_type_name(property_):
    _PROPERTY_TYPE_NAME_BY_PROPERTY_TYPE = \
        {type_: type_name for type_name, type_ in PROPERTY_TYPE_BY_NAME.items()}

    property_type = property_.__class__
    property_type_name = _PROPERTY_TYPE_NAME_BY_PROPERTY_TYPE[property_type]
    return property_type_name


def _get_raw_property_options(property_):
    from hubspot.contacts.properties import BooleanProperty
    from hubspot.contacts.properties import EnumerationProperty

    if isinstance(property_, BooleanProperty):
        raw_options_data = [
            {'label': property_.true_label, 'value': 'true', 'displayOrder': 0},
            {
                'label': property_.false_label,
                'value': 'false',
                'displayOrder': 1,
                },
            ]
    elif isinstance(property_, EnumerationProperty):
        raw_options_data = []
        for option_value, option_label in property_.options.items():
            option_data = {
                'label': option_label,
                'value': option_value,
                'displayOrder': 0,
                }
            raw_options_data.append(option_data)
    else:
        raw_options_data = []

    return raw_options_data
