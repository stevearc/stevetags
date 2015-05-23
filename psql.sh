#!/bin/bash -e
DB_NAME="stevetags-db"
export PGPASSWORD="postgres"

main() {
  docker run --rm --name psql -it -e PGPASSWORD --link "$DB_NAME:postgres" \
    postgres:9.4.1 /bin/bash -c \
    'exec psql -h "$POSTGRES_PORT_5432_TCP_ADDR" -p "$POSTGRES_PORT_5432_TCP_PORT" -U postgres'
}

main "$@"
