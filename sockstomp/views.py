

from pyramid.view import view_config, forbidden_view_config
from sockstomp.models import User
from pyramid.httpexceptions import HTTPForbidden, HTTPInternalServerError, HTTPUnauthorized
from pyramid.security import remember

from sockstomp.stomp.frames import (
    StompConnectedFrame,
    StompErrorFrame,
    )
from sockstomp.stomp.http import StompResponse
from pyramid.response import Response

d='-'*50

@view_config(name='', route_name='stomp',
             request_method='CONNECT')
def stomp_connect(request):
    req_headers = request.headers
    username = req_headers.get('X-STOMP-login')
    password = req_headers.get('X-STOMP-passcode')

    user = User.by_username(request.db, username)
    if user is None or not user.validate_password(password):
        raise HTTPUnauthorized()
    
    res_headers = remember(request, user.id, session=123)
    return StompResponse(command='CONNECTED', headerlist=res_headers)

@view_config(name='', route_name='stomp',
             permission='subscribe', request_method='SUBSCRIBE')
def stomp_subscribe(request):
    print d, 'stomp_subscribe', dict(request.headers)
    return Response()


@view_config(name='', route_name='stomp',
             permission='unsubscribe', request_method='UNSUBSCRIBE')
def stomp_unsubscribe(request):
    print d, 'stomp_unsubscribe'
    return Response()


@view_config(name='', route_name='stomp',
             permission='send', request_method='SEND')
def stomp_send(request):
    print d, 'stomp_send'
    return Response()

# oauth2 login views
# ------------------

from velruse import login_url

@view_config(route_name='providers', renderer='json')
def get_providers(request):
    """external auth provider list

    simple REST getter for a list of all registered auth providers.
    """
    return {
        'providers': [{
            'name': provider.name,
            'url': login_url(request, provider.name),
            'scope': provider.scope
        } for provider in request.registry.velruse_providers.values()]
    }

@view_config(context='velruse.providers.github.GithubAuthenticationComplete')
def login_complete_view(request):
    """handle github login

    shadows velruse view registered on inclusion. make sure to include
    before _scanning_ this callable.
    """
    # TODO
    # ----
    # mokeypatch velruse add_<provider>_login methods in order to decorate
    # the registered views with a pseudo session object set onto the request.
    # we don't want sessions at all. the session should always go into the JWT.
    context = request.context
    profile = context.profile
    provider_name = context.provider_name

    username = profile.get('preferredUsername', profile['displayName'])
    provider_id = [account['userid'] for account in profile['accounts'] \
                   if account['username'] == username][0]

    dbsession = request.db
    user = dbsession\
        .query(User)\
        .filter(User.provider_name==provider_name, User.provider_id==provider_id)\
        .first()

    if user is None:
        # users logged in via external auth providers don't have
        # a password but an oauth-access-token instead
        user = User(username, '', provider_id=provider_id, **context.__dict__)
        user.password = None
        dbsession.add(user)
        dbsession.commit()

    # TODO
    # ----
    # get the `state` alias sockjs-session-id from the GET parameters
    # to retrieve it and respond to the CONNECT request with
    # the appropriate CONNECTED request and the jwt-token attached
    # 
    # the `state` needs be piped by velruse.providers.github.GithubProvider#login
    # from the POST parameters to the github request. github will set that
    # `state` value onto the GET parameters when redirecting to our callback url.
    # 
    # the intial POST parameter `state` needs be extracted on the clientside
    # from sockjs' instance url property.
    # 
    # the big picture: we reuse the CSRF `state` oAuth parameter to identify
    # a sockjs session.
    # 
    # 1. connect over sockjs via stomp
    # 2. retrieve `state` param from sockjs endpoint path instead of a cookie
    # 3. POST `state` to our redirecting view namely
    #    velruse.providers.github.GithubProvider#login
    # 3.1 have that view monkeypatched in order to use the POST param `state`
    #    instead of the cookie!
    # 4. make that view pipe `state` to the external auth provider
    # 5. on redirection back from the provider extract `state` from the GET
    #    parameters
    # 6. identify the sockjs session from `request.stomp_manager[state]`
    # 7. generate the JWT and send a stomp CONNECTED frame in response to the
    #    initial CONNECT.
    #    
    # keep in mind that we will want to provide our own registration/authentication
    # procedure
    # 
    # extract the stomp sockjs session id / `state` like so
    # ```js
    # sockjs.addEventListener('open', function(){
    #   console.log(sockjs._transport.url.match(/__sockjs__\/.*?\/(.+?)\//))
    # });
    # ```
    # then set it onto a hidden form input value
    # 
    # -----------
    # velruse.providers.github.GithubProvider#callback's comparison
    # of the session's state and the state GET parameter does not really make
    # sense since the session is restored from the cookie set onto the request
    # originating from the POST

    return Response('<script>window.close()</script>')

@view_config(context='velruse.AuthenticationDenied', renderer='json')
def login_denied_view(request):
    return {'result': 'denied'}