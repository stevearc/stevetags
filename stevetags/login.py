""" Views for logging in """
import logging
from dropbox.client import DropboxOAuth2Flow
from pyramid.httpexceptions import HTTPFound, HTTPClientError, HTTPForbidden
from pyramid.security import forget, remember, NO_PERMISSION_REQUIRED
from .models import User
from pyramid.view import view_config


LOG = logging.getLogger(__name__)


@view_config(route_name='logout', permission=NO_PERMISSION_REQUIRED)
def logout(request):
    """ Remove stored user credentials from cookies. """
    request.response.headers.extend(forget(request))
    request.session.pop('access_token', None)
    return request.response


def get_auth_flow(request):
    key = request.registry.dropbox_key
    secret = request.registry.dropbox_secret
    redirect_url = request.route_url('dropbox_auth_finish')
    return DropboxOAuth2Flow(key, secret, redirect_url,
                             request.session, 'dropbox-auth-csrf-token')


@view_config(route_name='login', permission=NO_PERMISSION_REQUIRED)
@view_config(route_name='dropbox_auth_start',
             permission=NO_PERMISSION_REQUIRED)
def dropbox_auth_start(request):
    authorize_url = get_auth_flow(request).start()
    return HTTPFound(location=authorize_url)


@view_config(route_name='dropbox_auth_finish',
             permission=NO_PERMISSION_REQUIRED,
             renderer='onlogin.jinja2')
def dropbox_auth_finish(request):
    # TODO handle all of the exception cases
    try:
        access_token, userid, url_state = \
            get_auth_flow(request).finish(request.params)
    except DropboxOAuth2Flow.BadRequestException as e:
        return HTTPClientError()
    except DropboxOAuth2Flow.BadStateException as e:
        return HTTPFound(location=request.route_url('login'))
    except DropboxOAuth2Flow.CsrfException as e:
        return HTTPForbidden()
    except DropboxOAuth2Flow.NotApprovedException as e:
        return HTTPFound(location=request.route_url('root'))
    except DropboxOAuth2Flow.ProviderException as e:
        LOG.exception("Auth error")
        return HTTPForbidden()
    request.response.headers.extend(remember(request, userid))
    request.session['access_token'] = access_token
    account_info = request.dropbox.account_info()
    email = account_info['email']
    display_name = account_info['display_name']
    familiar_name = account_info['name_details']['familiar_name']
    user = User(userid, email, display_name, familiar_name)
    request.db.merge(user)
    # TODO: kick off a file refresh
    return {
        'error': None,
        'user': user,
    }
