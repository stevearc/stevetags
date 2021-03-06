#!/bin/bash -ex
VENV="{{ venv }}"
UWSGI_VENV="{{ uwsgi.venv }}"
UWSGI_LOG="{{ uwsgi.log }}"
UWSGI_CONFIG="{{ uwsgi.emperor_configs }}"


main() {
  apt-get update -qq
  apt-get -y install nginx-full libpq-dev
  wget -qO- https://get.docker.com/ | sh
  rm -f /etc/nginx/sites-enabled/default /etc/nginx/sites-available/default
  if [ ! -e "$VENV" ]; then
    mkdir -p "$(dirname $VENV)"
    virtualenv "$VENV"
  fi
  $VENV/bin/pip install pastescript
  if [ ! -e "$UWSGI_VENV" ]; then
    mkdir -p "$(dirname $UWSGI_VENV)"
    virtualenv "$UWSGI_VENV"
  fi
  /envs/emperor/bin/pip install uwsgi
  /envs/emperor/bin/pip install pastescript

  if [ ! -L /etc/nginx/sites-enabled/stevetags ]; then
    ln -s ../sites-available/stevetags /etc/nginx/sites-enabled/stevetags
  fi
  mkdir -p $UWSGI_CONFIG
  mkdir -p $(dirname UWSGI_LOG)

  if [ ! -e /envs/aws ]; then
    virtualenv /envs/aws
  fi
  /envs/aws/bin/pip install awscli

  echo "BOOTSTRAP COMPLETE"
}

main "$@"
