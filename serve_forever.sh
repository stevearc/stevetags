#!/bin/bash -ex

cd $(dirname "$0")

DB_NAME="stevetags-db"
cleanup() {
  set +e
  docker rm -f "$DB_NAME"
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

  docker run --name "$DB_NAME" -e POSTGRES_PASSWORD=postgres -p 8889:5432 -d postgres:9.4.1
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
