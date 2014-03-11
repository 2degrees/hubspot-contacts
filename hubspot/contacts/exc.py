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
