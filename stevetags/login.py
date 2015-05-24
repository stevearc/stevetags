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


@view_config(route_name='delete')
def delete_account(request):
    request.db.delete(request.user)
    return logout(request)

@view_config(route_name='dropbox_auth_finish',
             permission=NO_PERMISSION_REQUIRED,
             renderer='onlogin.jinja2')
def dropbox_auth_finish(request):
    try:
        access_token, userid, _ = \
            get_auth_flow(request).finish(request.params)
    except DropboxOAuth2Flow.BadRequestException:
        request.response.status_code = 400
        return {'error': 'Bad request'}
    except DropboxOAuth2Flow.BadStateException:
        request.response.status_code = 400
        return {'error': 'Bad state'}
    except DropboxOAuth2Flow.CsrfException:
        request.response.status_code = 403
        return {'error': 'CSRF check failure'}
    except DropboxOAuth2Flow.NotApprovedException:
        request.response.status_code = 400
        return {'error': 'Not approved'}
    except DropboxOAuth2Flow.ProviderException:
        request.response.status_code = 403
        return {'error': 'Auth error'}
    request.response.headers.extend(remember(request, userid))
    request.session['access_token'] = access_token
    account_info = request.dropbox.account_info()
    email = account_info['email']
    display_name = account_info['display_name']
    familiar_name = account_info['name_details']['familiar_name']
    user = User(userid, email, display_name, familiar_name)
    request.db.merge(user)
    return {
        'error': None,
        'user': user,
    }
