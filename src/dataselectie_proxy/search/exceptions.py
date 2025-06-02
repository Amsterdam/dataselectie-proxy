from rest_framework import exceptions, status


class BadGateway(exceptions.APIException):
    """Render an HTTP 502 Bad Gateway."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "Connection failed (bad gateway)"
    default_code = "bad_gateway"
