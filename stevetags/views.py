""" General views """
from datetime import date, timedelta
from sqlalchemy import func
from pyramid_duh import argify
from dateutil.parser import parse
import logging
import traceback
from pyramid.httpexceptions import HTTPException, HTTPServerError, HTTPNotFound
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.settings import asbool
from pyramid.view import view_config
from .models import File, Directory, MIME_TYPES
from sqlalchemy import not_


LOG = logging.getLogger(__name__)


@view_config(
    route_name='root',
    permission=NO_PERMISSION_REQUIRED,
    renderer='index.jinja2')
def index_view(request):
    """ Root view '/' """
    secure = asbool(request.registry.settings.get('session.secure', False))
    request.response.set_cookie('CSRF-Token', request.session.get_csrf_token(),
                                secure=secure)
    prefix = request.registry.settings.get('pike.url_prefix', 'gen').strip('/')
    return {
        'prefix': '/' + prefix,
    }


@view_config(route_name='user', renderer='json')
def get_user(request):
    return {
        'user': request.user
    }


@view_config(route_name='user_settings')
@argify(settings=dict)
def set_user_settings(request, settings):
    if set(settings['roots']) != request.user.settings.roots:
        query = request.db.query(File).filter_by(ownerid=request.authenticated_userid)
        q2 = request.db.query(Directory).filter_by(ownerid=request.authenticated_userid)
        for root in settings['roots']:
            query = query.filter(not_(File.path.like(root + '%')))
            q2 = q2.filter(not_(Directory.path.like(root + '%')))
        query.delete(synchronize_session=False)
        q2.delete(synchronize_session=False)
    for key, value in settings.iteritems():
        setattr(request.user.settings, key, value)
    return request.response


@view_config(route_name='files', renderer='json')
def list_files(request):
    files = request.db.query(File).filter_by(tagged=False) \
        .order_by(File.modified.desc()).limit(10).all()
    return {
        'files': files
    }


def _walk(request, metadata):
    if metadata['is_dir']:
        path = metadata['path']
        if 'contents' not in metadata:
            metadata = request.dropbox.metadata(path)
        f = request.db.query(Directory).filter_by(
            ownerid=request.authenticated_userid,
            path=path).first()
        hash = metadata['hash']
        if f is not None:
            if f.hash == hash:
                pass
                # TODO: allow early return to make refresh faster.
                # Right now it interferes with the mark-and-sweep.
                # return
            else:
                f.hash = hash
        else:
            f = Directory(request.authenticated_userid, path, hash)
        for child in metadata['contents']:
            _walk(request, child)
    else:
        if not request.user.should_save_file(metadata):
            return
        modified = parse(metadata['modified'])
        path = metadata['path']
        mime_type = metadata.get('mime_type')
        if mime_type is not None and len(request.user.settings.filetypes) > 0:
            if not any((MIME_TYPES[ft](mime_type) for ft in
                        request.user.settings.filetypes)):
                return
        f = File(request.authenticated_userid, path, modified, mime_type)
    f.marked = True
    request.db.merge(f)


@view_config(route_name='children', renderer='json')
@argify
def get_children(request, path):
    if path.count('/') >= 2:
        return {
            'children': []
        }
    metadata = request.dropbox.metadata(path)
    if not metadata['is_dir']:
        return request.error('not_directory', "The path is not a directory")
    children = [f for f in metadata['contents'] if f['is_dir']]
    return {
        'children': children,
    }


@view_config(route_name='refresh', renderer='json')
def refresh_files(request):
    for root in request.user.settings.roots:
        metadata = request.dropbox.metadata(root)
        _walk(request, metadata)
    request.db.query(File) \
        .filter_by(ownerid=request.authenticated_userid, marked=False) \
        .delete(synchronize_session=False)
    request.db.query(Directory) \
        .filter_by(ownerid=request.authenticated_userid, marked=False) \
        .delete(synchronize_session=False)
    request.db.query(File) \
        .filter_by(ownerid=request.authenticated_userid) \
        .update({'marked': False}, synchronize_session=False)
    request.db.query(Directory) \
        .filter_by(ownerid=request.authenticated_userid) \
        .update({'marked': False}, synchronize_session=False)
    return {}


@view_config(route_name='save_tags')
@argify
def save_tags(request, path, tags):
    if len(tags) > 100:
        tags = tags[:100]
    f = request.db.query(File).filter_by(
        ownerid=request.authenticated_userid,
        path=path).one()
    f.tags = tags
    f.tagged = True
    return request.response


@view_config(route_name='mark_tagged')
@argify
def mark_tagged(request, path):
    request.db.query(File) \
        .filter_by(ownerid=request.authenticated_userid, path=path) \
        .update({'tagged': True})
    return request.response


@view_config(route_name='search', renderer='json')
@argify(begin=date, end=date)
def search(request, query, begin=None, end=None):
    if end is not None:
        end = end + timedelta(days=1)
    q = request.db.query(File) \
        .filter_by(ownerid=request.authenticated_userid)
    if query.strip():
        q = q.filter(File.search_text.op('@@')(func.plainto_tsquery(query)))
    if begin is not None:
        q = q.filter(File.modified > begin)
    if end is not None:
        q = q.filter(File.modified < end)
    q = q.order_by(File.modified.desc()).limit(10)
    return {
        'files': q.all()
    }


@view_config(context=HTTPNotFound, permission=NO_PERMISSION_REQUIRED)
def handle_404(context, request):
    """ Catch the 404 so we don't log an exception. """
    LOG.warn("404: %s", request.url)
    return context


@view_config(
    context=Exception,
    renderer='json',
    permission=NO_PERMISSION_REQUIRED)
@view_config(
    context=HTTPException,
    renderer='json',
    permission=NO_PERMISSION_REQUIRED)
def format_exception(context, request):
    """
    Catch all app exceptions and render them nicely.

    This will keep the status code, but will always return parseable json

    Returns
    -------
    error : str
        Identifying error key
    msg : str
        Human-readable error message
    stacktrace : str, optional
        If pyramid.debug = true, also return the stacktrace to the client

    """
    LOG.exception(context.message)
    # If no X-Csrf-Token, this was a direct request from the browser and we
    # shouldn't return JSON.
    if 'X-Csrf-Token' not in request.headers:
        if isinstance(context, HTTPException):
            return context
        else:
            return HTTPServerError(context.message)
    error = {
        'error': getattr(context, 'error', 'unknown'),
        'msg': context.message,
    }
    if asbool(request.registry.settings.get('pyramid.debug', False)):
        error['stacktrace'] = traceback.format_exc()
    request.response.status_code = getattr(context, 'status_code', 500)
    return error
