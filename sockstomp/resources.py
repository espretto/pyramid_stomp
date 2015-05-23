
from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    )

class StompResource(object):

    __acl__ = [
        (Allow, 'g:admin', ALL_PERMISSIONS)
        ]

    def __init__(self, request):
        print 'root factory', id(request)
        self.request = request

    def __getitem__(self, key):
        if key == 'echo':
            return {'__parent__':self}
        else:
            raise KeyError()
