##############################################################################
#
# Copyright (c) 2014-2017, 2degrees Limited.
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

from voluptuous import Any
from voluptuous import Schema

from hubspot.contacts.properties import PROPERTY_TYPE_BY_NAME

PROPERTY_RESPONSE_SCHEMA_DEFINITION = {
    'name': unicode,
    'type': Any(*PROPERTY_TYPE_BY_NAME.keys()),
    'options': [],
}

CREATE_PROPERTY_RESPONSE_SCHEMA = Schema(
    PROPERTY_RESPONSE_SCHEMA_DEFINITION,
    required=True,
    extra=True,
)

_GET_ALL_PROPERTIES_RESPONSE_SCHEMA_DEFINITION = [
    PROPERTY_RESPONSE_SCHEMA_DEFINITION,
]

GET_ALL_PROPERTIES_RESPONSE_SCHEMA = Schema(
    _GET_ALL_PROPERTIES_RESPONSE_SCHEMA_DEFINITION,
    required=True,
    extra=True,
)
