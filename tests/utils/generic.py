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

from uuid import uuid4 as get_uuid4


def get_uuid4_str():
    uuid4 = get_uuid4()
    return str(uuid4)


def convert_object_strings_to_unicode(object_):
    if isinstance(object_, str):
        object_converted = unicode(object_)
    elif isinstance(object_, (list, tuple)):
        object_converted = \
            [convert_object_strings_to_unicode(value) for value in object_]
    elif isinstance(object_, dict):
        object_converted = {}
        for key, value in object_.items():
            object_converted[convert_object_strings_to_unicode(key)] = \
                convert_object_strings_to_unicode(value)
    else:
        object_converted = object_

    return object_converted
