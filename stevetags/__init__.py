import os
import posixpath

import argparse
import calendar
import datetime
import json
import logging
import subprocess
from collections import defaultdict
from dropbox.client import DropboxClient
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import NewRequest, subscriber
from pyramid.httpexceptions import exception_response
from pyramid.renderers import JSON, render, render_to_response
from pyramid.session import check_csrf_token
from pyramid.settings import asbool
from pyramid_beaker import session_factory_from_settings
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker

from .models import Base, User


# pylint: disable=F0401,E0611
from zope.sqlalchemy import ZopeTransactionExtension
# pylint: enable=F0401,E0611

LOG = logging.getLogger(__name__)


def to_json(value):
    """ A json filter for jinja2 """
    return render('json', value)

json_renderer = JSON()  # pylint: disable=C0103
json_renderer.add_adapter(datetime.datetime, lambda obj, r:
                          1000 * calendar.timegm(obj.utctimetuple()))
json_renderer.add_adapter(datetime.date,
                          lambda obj, _: obj.isoformat())
json_renderer.add_adapter(defaultdict,
                          lambda obj, _: dict(object))


@subscriber(NewRequest)
def check_csrf(event):
    """ Check the CSRF token on all non-GET requests. """
    request = event.request
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
        check_csrf_token(event.request)

def _user(request):
    return request.db.query(User).filter_by(id=request.authenticated_userid).first()

def _error(request, error, message='Unknown error', status_code=400):
    """
    Construct an error response

    Parameters
    ----------
    error : str
        Identifying error key
    message : str, optional
        Human-readable error message
    status_code : int, optional
        HTTP return code (default 500)

    """
    data = {
        'error': error,
        'msg': message,
    }
    LOG.error("%s: %s", error, message)
    request.response.status_code = status_code
    return render_to_response('json', data, request)


def _raise_error(request, error, message='Unknown error', status_code=400):
    """
    Raise an error response.

    Use this when you need to return an error to the client from inside of
    nested function calls.

    Parameters
    ----------
    error : str
        Identifying error key
    message : str, optional
        Human-readable error message
    status_code : int, optional
        HTTP return code (default 500)

    """
    err = exception_response(status_code, detail=message)
    err.error = error
    raise err


def _dropbox(request):
    access_token = request.session.get('access_token')
    if access_token is None:
        return request.forbid()
    return DropboxClient(access_token)


def _assets(request, key):
    """
    Get a list of built assets.

    Asset list pulled from files.json, which is written by build.go

    Parameters
    ----------
    key : str
        String identifier for a list of assets

    """
    filename = os.path.join(os.path.dirname(__file__), 'files.json')
    settings = request.registry.settings
    debug = asbool(settings.get('pike.debug', False))
    if debug or request.registry.assets is None:
        with open(filename, 'r') as ifile:
            request.registry.assets = json.load(ifile)
    prefix = request.registry.settings.get('pike.url_prefix', 'gen').strip('/')
    for filename in request.registry.assets.get(key, []):
        yield posixpath.join(prefix, filename)


def _constants(request):
    """ Create a dictionary of declared client constants. """
    data = {}
    for k, v in request.registry.client_constants.iteritems():
        if callable(v):
            v = v(request)
        if v is not None:
            data[k] = v
    return data


def _auth_callback(userid, request):
    """ Get permissions for a userid """
    return ['default']


def _db(request):
    """ Access a sqlalchemy session """
    if request.registry.dbmaker is None:
        engine = engine_from_config(request.registry.settings,
                                    prefix='sql.')
        Base.metadata.create_all(bind=engine)
        request.registry.dbmaker = sessionmaker(
            bind=engine, extension=ZopeTransactionExtension())

    maker = request.registry.dbmaker
    session = maker()

    def cleanup(request):
        """ Close the session after the request """
        session.close()
    request.add_finished_callback(cleanup)

    return session


def includeme(config):
    """ Set up and configure the app """
    settings = config.get_settings()
    config.include('pyramid_tm')
    config.include('pyramid_beaker')
    config.include('pyramid_duh')
    config.include('stevetags.route')
    config.add_renderer('json', json_renderer)

    # Jinja2 configuration
    settings['jinja2.filters'] = {
        'static_url': 'pyramid_jinja2.filters:static_url_filter',
        'json': to_json,
    }
    settings['jinja2.directories'] = ['stevetags:templates']
    config.include('pyramid_jinja2')
    config.commit()

    # Beaker configuration
    settings.setdefault('session.type', 'cookie')
    settings.setdefault('session.httponly', 'true')
    config.set_session_factory(session_factory_from_settings(settings))

    config.registry.dbmaker = None

    # Special request methods
    config.add_request_method(_db, name='db', reify=True)
    config.add_request_method(_user, name='user', reify=True)
    config.add_request_method(_error, name='error')
    config.add_request_method(_raise_error, name='raise_error')
    config.add_request_method(_constants, name='client_constants')
    config.add_request_method(lambda r, *a, **k: r.route_url('root', *a, **k),
                              name='rooturl')
    config.add_request_method(lambda r, u: _auth_callback(u, r),
                              name='user_principals')

    def get_env_setting(key):
        if key in settings:
            return settings[key]
        return os.environ[key.upper().replace('.', '_')]
    config.registry.dropbox_key = get_env_setting('dropbox.key')
    config.registry.dropbox_secret = get_env_setting('dropbox.secret')
    config.add_request_method(_dropbox, name='dropbox', reify=True)

    prefix = settings.get('pike.url_prefix', 'gen').strip('/')
    config.registry.client_constants = {
        'URL_PREFIX': '/' + prefix,
        'USER': lambda r: r.user,
    }

    config.registry.assets = None
    config.add_request_method(_assets, name='assets')
    debug = asbool(settings.get('pike.debug', False))
    cache_age = 0 if debug else 31556926
    config.add_static_view(name=prefix,
                           path='stevetags:gen',
                           cache_max_age=cache_age)

    # Auth
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.set_authentication_policy(AuthTktAuthenticationPolicy(
        secret=settings['auth.secret'],
        cookie_name=settings.get('auth.cookie_name', 'auth_tkt'),
        secure=asbool(settings.get('auth.secure', False)),
        timeout=int(settings.get('auth.timeout', 60 * 60 * 24 * 30)),
        reissue_time=int(settings.get('auth.reissue_time', 60 * 60 * 24 * 15)),
        max_age=int(settings.get('auth.max_age', 60 * 60 * 24 * 30)),
        http_only=asbool(settings.get('auth.http_only', True)),
        hashalg='sha512',
        callback=_auth_callback,
    ))
    config.set_default_permission('default')

    config.scan()


def main(config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('stevetags')
    return config.make_wsgi_app()

def deploy():
    """ Deploy static files to a directory """
    parser = argparse.ArgumentParser(description=deploy.__doc__)
    parser.add_argument('dest', help="Destination directory")
    args = parser.parse_args()

    dest = os.path.abspath(args.dest)
    if not os.path.exists(dest):
        os.makedirs(dest)

    resources = os.path.join(os.path.dirname(__file__), 'gen')
    for filename in os.listdir(resources):
        src = os.path.join(resources, filename)
        subprocess.check_call(['cp', '-r', src, dest])
