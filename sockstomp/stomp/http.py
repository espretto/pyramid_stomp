
from pyramid.response import Response
from pyramid.request import Request
from .frames import StompFrame

STOMP_HEADER_PREFIX = 'X-STOMP-'
HTTP_HEADER_PREFIX = 'X-HTTP-'

class StompResponse(Response):

    def __init__(self, *args, **kw):
        self.command = kw.pop('command')
        super(StompResponse, self).__init__(*args, **kw)

    def as_stomp(self):
        stomp_headers = {}
        offset = len(STOMP_HEADER_PREFIX)
        for key, value in self.headerlist:
            if key.startswith(STOMP_HEADER_PREFIX):
                stomp_headers[key[offset:]] = value
            else:
                stomp_headers[HTTP_HEADER_PREFIX + key] = value

        return StompFrame(self.body, self.command, **stomp_headers)

class StompRequest(object):

    @classmethod
    def from_stomp(self, frame):
        headers = frame.headers
        path = headers.pop('destination')
        offset = len(HTTP_HEADER_PREFIX)

        http_headers = {}
        for key, value in headers.items():
            if key.startswith(HTTP_HEADER_PREFIX):
                http_headers[key[offset:]] = value
            else:
                http_headers[STOMP_HEADER_PREFIX + key] = value

        return Request.blank(path,
                             method=frame.command,
                             headers=http_headers,
                             json=frame.body,
                             content_type='application/json; charset=UTF-8'
                             )