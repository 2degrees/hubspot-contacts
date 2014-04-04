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

class HubspotException(Exception):
    pass


class HubspotUnsupportedResponseError(HubspotException):
    pass


class HubspotClientError(HubspotException):
    """Representation of a 40X error"""

    def __init__(self, msg, request_id):
        super(HubspotClientError, self).__init__(msg)

        self.request_id = request_id


class HubspotAuthenticationError(HubspotClientError):
    pass


class HubspotServerError(HubspotException):
    """Representation of a 50X error"""

    def __init__(self, msg, http_status_code):
        super(HubspotServerError, self).__init__(msg)

        self.http_status_code = http_status_code

    def __str__(self):
        return '{} {}'.format(self.http_status_code, self.message)


class HubspotPropertyValueError(HubspotException):
    pass
