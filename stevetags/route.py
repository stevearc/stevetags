""" Route configuration. """
from pyramid.security import Allow, Authenticated, DENY_ALL, ALL_PERMISSIONS


class Root(object):

    """
    Root context.

    Defines ACL, not much else.

    """
    __acl__ = [
        [Allow, 'admin', ALL_PERMISSIONS],
        [Allow, Authenticated, 'default'],
        DENY_ALL,
    ]

    def __init__(self, request):
        self.request = request


def includeme(config):
    """ Add the url routes """
    config.set_root_factory(Root)
    config.add_route('root', '/', request_method='GET')

    config.add_route('user', '/user', request_method='GET')
    config.add_route('user_settings', '/user/settings', request_method='POST')
    config.add_route('delete', '/user/delete', request_method='GET')

    config.add_route('files', '/files', request_method='GET')
    config.add_route('children', '/files/children', request_method='GET')
    config.add_route('search', '/files/search', request_method='GET')
    config.add_route('refresh', '/files/refresh', request_method='GET')
    config.add_route('save_tags', '/files/tags', request_method='POST')
    config.add_route('mark_tagged', '/files/tagged', request_method='POST')

    config.add_route('logout', '/logout', request_method='GET')
    config.add_route('login', '/login', request_method='GET')
    config.add_route('dropbox_auth_start', '/dropbox_auth_start', request_method='GET')
    config.add_route('dropbox_auth_finish', '/dropbox_auth_finish', request_method='GET')
