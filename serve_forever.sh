#!/bin/bash -ex
declare -r DOCKER_COMPOSE_VERSION="1.2.0"

cd $(dirname "$0")

DB_NAME="stevetags-db"
cleanup() {
  set +e
  docker-compose stop
  docker-compose rm -f -v
}
trap cleanup SIGINT SIGTERM EXIT

serve() {
  set +e
  while [ 1 ]; do
    pserve --reload development.ini
    sleep 1
  done
}

main() {
  ./dl-deps.sh

  if [ ! `which docker` ]; then
    wget -qO- https://get.docker.com/ | sh
  fi
  if [ ! `which docker-compose` ]; then
    local filename=$(mktemp)
    curl -L https://github.com/docker/compose/releases/download/$DOCKER_COMPOSE_VERSION/docker-compose-`uname -s`-`uname -m` > $filename
    chmod +x $filename
    sudo mv $filename /usr/local/bin/docker-compose
    local completion=$(mktemp)
    curl -L https://raw.githubusercontent.com/docker/compose/$DOCKER_COMPOSE_VERSION/contrib/completion/bash/docker-compose > $completion
    chmod 644 $completion
    sudo chown root:root $completion
    sudo mv $completion /etc/bash_completion.d/docker-compose
  fi

  rm -rf stevetags/gen/*
  rm -f stevetags/files.json
  go run build.go -w &

  if [ ! -e stevetags_env ]; then
    virtualenv stevetags_env
  fi
  . stevetags_env/bin/activate
  pip install -e .
  pip install fabric jinja2
  pip install waitress

  docker-compose up -d
  sleep 1 # Wait for the DB to come up
  serve &

  echo -e "\033[0;32mServer running! Use 'q' to quit\033[00m"

  local input=""
  while [ "$input" != "q" ]; do
    read -r input
  done
  kill 0
}

main "$@"
