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
