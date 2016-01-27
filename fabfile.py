import os

import fabric.api as fab
import jinja2
from fabric.colors import green
from fabric.context_managers import path
from fabric.decorators import roles, task


fab.env.roledefs = {
    'stevetags': ['stevearc@www.stevetags.com'],
}

CONSTANTS = {
    'venv': "/envs/stevetags",
    'db': {
        'user': 'postgres',
        'hostname': 'localhost',
        'database': 'postgres',
        'port': 8889,
        'container': 'stevetags-db',
    },
    'uwsgi': {
        'port': 3031,
        'num_processes': 10,
        'venv': "/envs/emperor",
        'emperor_configs': '/etc/emperor',
        'log': '/var/log/uwsgi/emperor.log',
    },
}


def _get_ref():
    ref = fab.local('git rev-parse HEAD', capture=True)
    return ref[:8]


def _get_var(key):
    if key not in os.environ:
        raise Exception("Missing environment variable %r" % key)
    return os.environ[key]


def _set_env_constants():
    CONSTANTS['dropbox'] = {
        'key': _get_var('DROPBOX_KEY'),
        'secret': _get_var('DROPBOX_SECRET'),
    }
    CONSTANTS['db']['password'] = _get_var('STEVETAGS_PG_PASS')
    CONSTANTS['asset_prefix'] = _get_ref()
    CONSTANTS['session'] = {
        'encrypt_key': _get_var('STEVETAGS_ENCRYPT_KEY'),
        'validate_key': _get_var('STEVETAGS_VALIDATE_KEY'),
    }
    CONSTANTS['auth_secret'] = _get_var('STEVETAGS_AUTH_SECRET')
_set_env_constants()


def _version():
    return fab.local('git describe --tags', capture=True)


def _render(filename, **context):
    with open(filename, 'r') as ifile:
        tmpl = jinja2.Template(ifile.read())
    basename = os.path.basename(filename)
    fab.local('mkdir -p dist')
    outfile = os.path.join('dist', basename)
    with open(outfile, 'w') as ofile:
        ofile.write(tmpl.render(**context))
    return outfile


def _render_put(filename, dest, **kwargs):
    rendered = _render(filename, **CONSTANTS)
    fab.put(rendered, dest, **kwargs)


NO_DEFAULT = object()


def prompt(msg, default=NO_DEFAULT, validate=None):
    """ Prompt user for input """
    while True:
        response = raw_input(msg + ' ').strip()
        if not response:
            if default is NO_DEFAULT:
                continue
            return default
        if validate is None or validate(response):
            return response


def promptyn(msg, default=None):
    """ Display a blocking prompt until the user confirms """
    while True:
        yes = "Y" if default else "y"
        if default or default is None:
            no = "n"
        else:
            no = "N"
        confirm = prompt("%s [%s/%s]" % (msg, yes, no), '').lower()
        if confirm in ('y', 'yes'):
            return True
        elif confirm in ('n', 'no'):
            return False
        elif len(confirm) == 0 and default is not None:
            return default


@task
def bundle():
    """ Bundle up assets into a tarball """
    fab.local('./dl-deps.sh')
    fab.local('rm -rf stevetags/gen stevetags/files.json')
    fab.local('go run build.go')
    version = _version()
    fab.local("sed -i -e 's/version=.*/version=\"%s\",/' setup.py" % version)
    fab.local('python setup.py sdist')
    fab.local("sed -i -e 's/version=.*/version=\"develop\",/' setup.py")
    print green("Created dist/stevetags-%s.tar.gz" % version)
    return version


@task
@roles('stevetags')
def deploy():
    """ Deploy the website """
    version = bundle()
    tarball = "stevetags-%s.tar.gz" % version
    fab.put("dist/" + tarball)

    with path(CONSTANTS['venv'] + '/bin', behavior='prepend'):
        fab.sudo("yes | pip uninstall stevetags || true")
        fab.sudo("pip install %s" % tarball)
        fab.sudo('st-deploy /var/nginx/stevetags/%s' %
                 CONSTANTS['asset_prefix'])
    _render_put('etc/stevetags.ini', '/etc/emperor/stevetags.ini',
                use_sudo=True)
    fab.run("rm " + tarball)
    print green("Deployed stevetags %s" % version)


@task
@roles('stevetags')
def reset_db():
    """ Remove and replace the DB """
    db = CONSTANTS['db']
    fab.sudo("docker rm -f %s || true" % db['container'])

    ret = fab.sudo("docker inspect --format=\"{{ .State.Running }}\" %s" %
                   db['container'], quiet=True, warn_only=True)
    if ret.return_code != 0:
        print green("No DB container found. Creating one now...")
        fab.sudo("docker run --name '%s' -e 'POSTGRES_PASSWORD=%s' "
                 "-p %d:5432 -d postgres:9.4.1" %
                 (db['container'], db['password'], db['port']))
    elif ret != 'true':
        print green("DB container is stopped. Restarting...")
        fab.sudo("docker start '%s'" % db['container'])


@task
@roles('stevetags')
def bootstrap():
    """ Bootstrap a new server (Ubuntu 14.04) """
    db = CONSTANTS['db']
    _render_put('bootstrap.sh', 'bootstrap.sh')
    fab.run("chmod +x bootstrap.sh")
    fab.sudo("./bootstrap.sh")
    fab.run("rm bootstrap.sh")
    _render_put('etc/stevetags.site', '/etc/nginx/sites-available/stevetags',
                use_sudo=True)
    fab.sudo("service nginx reload")
    _render_put('etc/uwsgi.conf', '/etc/init/uwsgi.conf', use_sudo=True)
    fab.sudo("service uwsgi restart")
    fab.run('echo %s > PGPASSWORD' % db['password'])
    fab.run('chmod 600 PGPASSWORD')
    fab.put('dump.sh')
    fab.put('db_backup', '/etc/cron.d/db_backup', use_sudo=True)
    print "Need to add aws credentials for database backup cronjob"


@task
@roles('stevetags')
def psql():
    """ Connect to the db with psql """
    fab.sudo("docker run --rm -it -e \"PGPASSWORD=%s\" --link "
             "\"%s:postgres\" postgres:9.4.1 "
             "/bin/bash -c 'exec psql -h "
             "\"$POSTGRES_PORT_5432_TCP_ADDR\" -p "
             "\"$POSTGRES_PORT_5432_TCP_PORT\" -U postgres'"
             % (CONSTANTS['db']['password'], CONSTANTS['db']['container']))


@task
@roles('stevetags')
def pg_dump(format='p'):
    """ Get a pg_dump of the database """
    assert format in ['c', 'd', 't', 'p']
    db = CONSTANTS['db']
    fab.sudo("docker run --rm -it -e \"PGPASSWORD=%s\" --link "
             "\"%s:postgres\" -v /tmp:/mnt postgres:9.4.1 "
             "/bin/bash -c 'exec pg_dump -c --format=%s -f /mnt/dump.sql "
             "-h \"$POSTGRES_PORT_5432_TCP_ADDR\" "
             "-p \"$POSTGRES_PORT_5432_TCP_PORT\" -U postgres'"
             % (db['password'], db['container'], format))
    if promptyn(green("Dumped to /tmp/dump.sql. Fetch it?"), default=True):
        fab.get("/tmp/dump.sql")
