
from . import VERSION
from .parser import create_parser

stomp_parser = create_parser()


class StompFrame(object):
    command = None

    def __init__(self, body='', command=None, **headers):
        self.command = self.command or command
        if self.command is None:
            raise StompFormatException('missing command')
        self.body = body
        self.headers = {k.replace('_', '-'): v for k,v in headers.items()}
        self.headers.setdefault('server', 'gevent')

    @classmethod
    def from_message(cls, message):
        """

        https://stomp.github.io/stomp-specification-1.2.html#Augmented_BNF
        """
        # re-raise exception to hide pyparsing specific exception
        try:
            parsed_message = stomp_parser.parseString(message)
        except ParseBaseException, e:
            raise StompParseException(e.message)

        parts = parsed_message.asList()
        body = parts.pop()
        command = parts.pop(0)
        headers = {header[0]: header[1] for header in parts}

        return cls(body, command, **headers)

    def __unicode__(self):
        headers = '\n'.join(['%s:%s' % (k, v)
                            for k, v in self.headers.items()])
        return '%s\n%s\n\n%s\0' % (self.command, headers, self.body)

    def __str__(self):
        return unicode(self).encode('UTF-8')

# shortcut constructors
# ---------------------
# for outgoing stomp messages only

class StompErrorFrame(StompFrame):
    command = 'ERROR'

class StompConnectedFrame(StompFrame):
    command = 'CONNECTED'

class StompReceiptFrame(StompFrame):
    command = 'RECEIPT'

class StompMessageFrame(StompFrame):
    command = 'MESSAGE'

# stomp exceptions
# ----------------

class StompException(Exception):
    pass

class StompParseException(StompException):
    pass

class StompFormatException(StompException):
    pass