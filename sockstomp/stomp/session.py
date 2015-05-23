
import uuid

from pyramid.request import Request
from pyramid.events import ApplicationCreated, subscriber
from pyramid_sockjs.session import SessionManager, Session
from sqlalchemy.exc import DBAPIError
from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE

from sockstomp.models import User
from . import VERSION as STOMP_VERSION, ACK_MODES
from .frames import (
    StompConnectedFrame,
    StompErrorFrame,
    StompFrame,
    StompMessageFrame,
    StompParseException,
    StompReceiptFrame,
    )
from .http import StompResponse

@subscriber(ApplicationCreated)
def setup_cache(event):
    """
    Sorry this is a little convoluted, but it's a common question and
    the best answer is: pass the configurator to your submodules
    that need it and allow them to add stuff to
    the registry/settings objects for use later.
    """
    StompTransaction.cache = make_region().configure_from_config(
        event.app.registry.settings,
        'dogpile.memcached.' # prefix
        )


class StompTransaction():

    cache = None

    def __init__(self, session_id, transaction_id):
        self.session_id = session_id
        self.transaction_id = transaction_id
        self.keys = []

    def _generate_key(self, n):
        return '%s:%s:%d' % (
            self.session_id,
            self.transaction_id,
            len(self.keys)
            )

    def invalidate(self):
        self.cache.delete_multi(self.keys)

    def get_frames(self):
        return self.cache.get_multi(self.keys)

    def add_frame(self, frame):
        key = self._generate_key()
        self.keys.append(key)
        self.cache.set(key, unicode(frame))


class StompSession(Session):
    """stomp session

    see: http://stomp.github.io/stomp-specification-1.1.html
    and: http://jmesnil.net/stomp-websocket/doc/

    stomp handlers responding to incoming messages
    are prefixed 'on_stomp_'
    """
    def __init__(self, *args, **kwargs):
        super(StompSession, self).__init__(*args, **kwargs)
        self.transactions = {}

    def on_open(self):
        pass

    def on_close(self):
        pass

    def on_remove(self):
        for transaction in self.transactions.values():
            transaction.invalidate()

    def on_message(self, stomp_message):
        """stomp message sink

        main entry point for stomp messages.
        """
        try:
            input_frame = StompFrame.from_message(stomp_message)
        except StompParseException, e:
            self.send(unicode(StompErrorFrame(e.message)))
            self.close()
        else:
            self.on_frame(input_frame)

    def on_frame(self, input_frame):
        """stomp frame sink

        entry point for stomp frames, especially cached ones
        from within a transaction.
        """
        command = input_frame.command.lower()
        handler = getattr(self, 'on_stomp_%s' % command)
        output_frame = handler(input_frame)

        receipt = input_frame.headers.get('receipt')
        if receipt is not None:
            output_frame = output_frame or StompReceiptFrame()
            output_frame.headers['receipt-id'] = receipt
        
        if output_frame is not None:
            self.send(unicode(output_frame))
            if isinstance(output_frame, StompErrorFrame):
                self.close()

    def on_stomp_connect(self, input_frame):
        """connect to stomp broker

        handles authentication and version negotiation
        """
        headers = input_frame.headers
        versions = headers.get('accept-version')

        if versions is None or not STOMP_VERSION in versions.split(','):
            return StompErrorFrame(message='unsupported version', 
                                   version=STOMP_VERSION)
        elif not 'login' in headers:
            return StompErrorFrame(message='missing header login')
        elif not 'passcode' in headers:
            return StompErrorFrame(message='missing header passcode')

        output_frame = self.handle_as_request(input_frame)

        output_frame.headers.setdefault('heart-beat', '0,0')
        output_frame.headers['version'] = STOMP_VERSION
        return output_frame
          
    def on_stomp_disconnect(self, input_frame):
        """disconnect client

        if a 'receipt' was provided by the client
        ``on_frame`` will take care as it will on all requests.
        """
        pass

    def on_stomp_send(self, input_frame):
        """receive client message

        'destination' header is required.
        if the 'transaction' header is provided the message will
        be memcached and fetched later when the transaction is committed
        or removed when aborted.
        """
        headers = input_frame.headers
        tid = headers.get('transaction')
        destination = headers.get('destination')

        if destination is None:
            return StompErrorFrame(message='missing destination header')
        elif tid is None:
            return self.handle_as_request(input_frame)
        elif tid in self.transactions:
            self.transactions[tid].add_frame(input_frame)
        else:
            return StompErrorFrame(message='missing transaction %s' % tid)

    def on_stomp_begin(self, input_frame):
        """start a stomp transaction

        if no 'transaction' header is provided we generate one.
        calls to ``stomp_send`` including a transaction header will
        contribute to it and be processed/passed to ``on_frame`` when committed.
        """
        tid = input_frame.headers.get('transaction', uuid.uuid4())
        
        if tid in self.transactions:
            return StompErrorFrame(message='transaction already begun',
                                   transaction=tid)
        else:
            self.transactions[tid] = StompTransaction(self.id, tid)
        
    def on_stomp_abort(self, input_frame):
        """abort stomp transaction

        requires the 'transaction' header. removes the transaction from cache.
        """
        tid = input_frame.headers.get('transaction')
        
        if tid is None:
            return StompErrorFrame(message='missing transaction header')
        elif not tid in self.transactions:
            return StompErrorFrame(message='transaction unknown',
                                   transaction=tid)
        else:
            self.transactions[tid].invalidate()
            del self.transactions[tid]

    def on_stomp_commit(self, input_frame):
        """commit stomp transaction

        requires the 'transaction' header. pops the transaction from cache
        and processes all frames/passes them to ``on_frame``.
        """
        tid = input_frame.headers.get('transaction')

        if tid is None:
            return StompErrorFrame(message='missing transaction header')
        elif not tid in self.transactions:
            return StompErrorFrame(message='transaction unknown',
                                   transaction=tid)
        else:
            transaction = self.transactions[tid]
            frames = transaction.get_frames()
            
            if NO_VALUE in frames:
                return StompErrorFrame(message='transaction expired',
                                       transaction=tid)
            
            for frame in frames:
                del frame.headers['transaction']
                self.on_frame(frame)

            transaction.invalidate()
            del self.transactions[tid]
                    

    def on_stomp_subscribe(self, input_frame):
        """subscribe to destination

        'id' and 'destination' headers are required.
        """
        headers = input_frame.headers
        ack_mode = headers.get('ack', 'auto')
        # TODO validate id is md5 of destination and any additional
        # query parameters for the subscription

        if not ack_mode in ACK_MODES:
            return StompErrorFrame(message='invalid acknowledgement mode')
        elif not 'id' in headers:
            return StompErrorFrame(message='missing id header')
        elif not 'destination' in headers:
            return StompErrorFrame(message='missing destination header')
        else:
            return self.handle_as_request(input_frame)

    def on_stomp_unsubscribe(self, input_frame):
        """unsubscribe from destination

        subscription 'id' header is required
        """
        if not 'id' in input_frame.headers:
            return StompErrorFrame(message='missing id header')
        else:
            return self.handle_as_request(input_frame)

    def on_stomp_ack(self, input_frame):
        """acknowledge a message"""
        headers = input_frame.headers
        mid = headers.get('id')
        tid = headers.get('transaction')

        # TODO:
        # lookup transaction/message
        # diff between auto | client | client-individual
        # act accordingly
        
        raise NotImplemented()

    def on_stomp_nack(self, input_frame):
        """negative acknowledge a message"""
        headers = input_frame.headers
        mid = headers.get('id')
        tid = headers.get('transaction')

        # TODO:
        # lookup transaction/message
        # diff between auto | client | client-individual
        # act accordingly
        
        raise NotImplemented()

    # endpoints
    # ---------

    def handle_as_request(self, input_frame):
        from pyramid.httpexceptions import HTTPError
        from .http import StompRequest, StompResponse

        # TODO
        # ----
        # subclass pyramid.request.Request to set the frame on it.
        # introduce another `from_stomp_frame` method and attributes
        # `stomp_headers`, `stomp_body`, `stomp_method` and `stomp_json`
        # as well as an appropriate view predicate!
        request = StompRequest.from_stomp(input_frame)

        try:
            response = self.request.invoke_subrequest(request)
            if isinstance(response, StompResponse):
                return response.as_stomp()
        except HTTPError, e:
            from json import dumps
            body = dumps({k: getattr(e, k) for k in ['explanation', 'detail']})
            return StompErrorFrame(body, message=e.title)
        # DEBUG
        except:
            return StompErrorFrame(message='internal error')


    def send_stomp(self, frame, await_ack=False):
        """send stomp message to client

        this is the only handler that doesn't respond directly
        to a previous message
        """
        raise NotImplemented()

        # TODO: lookup subscription/transaction mode
        # (auto | client | client-individual)
        # and cache appropriately
        # 
        # create and pack frame from the manager so that
        # not every god damn session has to do it itself.
        # output_frame = StompMessageFrame('MESSAGE', body,
        #     subscription=sid,
        #     destination=self.manager.prefix + dest,
        #     content_type=content_type,
        #     content_length=len(body),
        #     message_id=uuid.uuid4(),
        #     )

        # self.send(output_frame.pack())
        # 
        # START by reading http://docs.pylonsproject.org/projects/pyramid-cookbook/en/latest/routing/index.html


class StompSessionManager(SessionManager):
    def __init__(self, *args, **kwargs):
        super(StompSessionManager, self).__init__(*args, **kwargs)
