
from pyparsing import (
    CharsNotIn,
    dictOf,
    LineEnd,
    oneOf,
    Optional,
    Or,
    ParserElement,
    SkipTo,
    StringEnd,
    StringStart,
    Suppress,
    ZeroOrMore,
    ParseBaseException,
    )

from . import (
    CLIENT_COMMANDS,
    SERVER_COMMANDS,
    )

def create_parser():
    """creates stomp message parser

    implementation of stomp's BNF specification:

    NULL            = <US-ASCII null (octet 0)>
    LF              = <US-ASCII line feed (aka newline) (octet 10)>
    CR              = <US-ASCII carriage return (octet 13)>
    EOL             = [CR] LF 
    OCTET           = <any 8-bit sequence of data>

    frame-stream    = 1*frame

    frame           = command EOL
                      *( header EOL )
                      EOL
                      *OCTET
                      NULL
                      *( EOL )

    command         = client-command | server-command

    client-command  = "SEND"
                    | "SUBSCRIBE"
                    | "UNSUBSCRIBE"
                    | "BEGIN"
                    | "COMMIT"
                    | "ABORT"
                    | "ACK"
                    | "NACK"
                    | "DISCONNECT"
                    | "CONNECT"
                    | "STOMP"

    server-command  = "CONNECTED"
                    | "MESSAGE"
                    | "RECEIPT"
                    | "ERROR"

    header          = header-name ":" header-value
    header-name     = 1*<any OCTET except CR or LF or ":">
    header-value    = *<any OCTET except CR or LF or ":">
    """

    ParserElement.setDefaultWhitespaceChars('')

    delimiters = '\0\r\n:'

    NULL, CR, LF, COLON = map(Suppress, delimiters)
    EOL = Optional(CR) + LF

    command = oneOf(CLIENT_COMMANDS) ^ oneOf(SERVER_COMMANDS)
    header_name = CharsNotIn(delimiters[1:])
    header_value = Optional(header_name)
    headers = dictOf(header_name + COLON,
                     header_value + EOL)

    return StringStart()\
         + command + EOL\
         + headers + EOL\
         + SkipTo(NULL + ZeroOrMore(EOL) + StringEnd())
