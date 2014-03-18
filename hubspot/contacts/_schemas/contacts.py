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

from voluptuous import All
from voluptuous import Length
from voluptuous import Optional
from voluptuous import Schema

from hubspot.contacts._schemas._validators import AnyListItemValidates
from hubspot.contacts._schemas._validators import Constant
from hubspot.contacts._schemas._validators import DynamicDictionary
from hubspot.contacts._schemas._validators import GetDictValue


_CANONICAL_IDENTITY_PROFILE_SCHEMA = {
    'vid': int,
    'identities': All(
        [],
        AnyListItemValidates(
            Schema(
                {'type': Constant(u'EMAIL'), 'value': unicode},
                required=True,
                extra=True,
                ),
            ),
        ),
    }

_IS_PROPERTY_VALUE = Schema({'value': unicode}, required=True, extra=True)

CONTACTS_PAGE_SCHEMA = Schema(
    {
        'contacts': [{
            'vid': int,
            'properties': DynamicDictionary(
                unicode,
                All(_IS_PROPERTY_VALUE, GetDictValue('value')),
                ),
            'identity-profiles': All(
                [{'vid': int, 'identities': []}],
                Length(min=1),
                AnyListItemValidates(_CANONICAL_IDENTITY_PROFILE_SCHEMA),
                ),
            }],
        'has-more': bool,
        'vid-offset': int,
        Optional('time-offset'): int,
        },
    required=True,
    extra=True,
    )
