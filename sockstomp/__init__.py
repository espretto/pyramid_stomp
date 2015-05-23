
from pyramid.config import Configurator
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    )
from pyramid_jwtauth import JWTAuthenticationPolicy
from velruse import app as velruse_app

from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker

from sockstomp.stomp.session import (
    StompSession,
    StompSessionManager
    )


# middlware
# ---------

def db(request):
    """
    create a database session per request and populates it onto it
    access it via `request.db` from within your views
    """
    session = request.registry.DBSession()

    def cleanup(request):
        if request.exception is not None:
            session.rollback()
        else:
            session.commit()
        session.close()

    request.add_finished_callback(cleanup)
    return session


class CustomJWTAuthenPolicy(JWTAuthenticationPolicy):

    def remember(self, request, principal, **claims):
        claims[self.userid_in_claim] = principal
        token = self.encode_jwt(request, claims)
        return [('JWT', token)]


# baseline setup
# --------------

def main(global_config, **settings):
    config = Configurator(settings=settings)

    # auth providers
    # --------------
    config.include(velruse_app)
    config.add_route('providers', '/providers/')

    # authorization
    # -------------
    author_policy = ACLAuthorizationPolicy()
    config.set_authorization_policy(author_policy)

    # authentication
    # --------------
    authen_policy = CustomJWTAuthenPolicy.from_settings(settings, prefix='jwtauth.')
    config.set_authentication_policy(authen_policy)
    config.add_forbidden_view(lambda request: authen_policy.challenge(request))

    # database setup
    # --------------
    engine = engine_from_config(settings, prefix='sqlalchemy.')
    engine.pool._use_threadlocal = True
    config.registry.DBSession = sessionmaker(bind=engine)
    config.add_request_method(db, reify=True)

    # sockjs
    # ------
    config.include('pyramid_sockjs')
    stomp_manager = StompSessionManager('stomp', config.registry, StompSession)

    config.add_sockjs_route(name='stomp',
                            prefix='/__sockjs__',
                            cookie_needed=False, per_user=False,
                            session_manager=stomp_manager)

    config.add_request_method(lambda req: stomp_manager, 'stomp_manager')

    # router
    # ------
    config.add_route('stomp', '/stomp/*traverse',
                     factory='sockstomp.resources.StompResource');

    config.scan()

    # recursively import .models package one level deep
    # config.scan('sockstomp.models')
    
    # dev spec static files
    # =====================
    # this must be registered after `config.scan()`
    config.add_static_view(name='static', path='./client')

    return config.make_wsgi_app()
