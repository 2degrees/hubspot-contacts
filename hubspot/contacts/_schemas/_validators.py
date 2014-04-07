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

from functools import wraps

from voluptuous import All
from voluptuous import Invalid
from voluptuous import Schema


def GetDictValue(dict_key):
    """ Replace a dictionary with the value of 'dict_key' """
    @wraps(GetDictValue)
    def _get_dict_value(value):
        try:
            dict_value = value[dict_key]
        except KeyError:
            raise Invalid('expected key {!r} in dictionary'.format(dict_key))
        except TypeError:
            raise Invalid('expected a dictionary')
        return dict_value

    return _get_dict_value


def DynamicDictionary(keys_validator, values_validator):
    """ Validate a dictionary with unknown (dynamic) items """
    keys_schema = Schema(keys_validator)
    values_schema = Schema(values_validator)

    @wraps(DynamicDictionary)
    def _validate(dictionary):
        validated_dictionary = {
            keys_schema(k): values_schema(v) for k, v in dictionary.items()
            }
        return validated_dictionary

    return All(Schema({}, extra=True), _validate)


def AnyListItemValidates(list_item_validator):
    """
    Validate that at least one item in the list complies with
    'list_item_validator'.

    """
    @wraps(AnyListItemValidates)
    def _validate(value):
        if not isinstance(value, list):
            raise Invalid('expected a list')

        list_item_schema = Schema(list_item_validator)
        validated_values_list = []
        is_valid = False
        for v in value:
            try:
                validated_value = list_item_schema(v)
            except Invalid:
                validated_values_list.append(v)
            else:
                validated_values_list.append(validated_value)
                is_valid = True
        if not is_valid:
            raise Invalid('no list item validates')

        return validated_values_list

    return _validate


def Constant(expected_value):
    @wraps(Constant)
    def _validate(value):
        if value != expected_value:
            raise Invalid('expected {!r}'.format(expected_value))

        return value

    return _validate
