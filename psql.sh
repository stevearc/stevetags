#!/bin/bash -e
export PGPASSWORD="postgres"

main() {
  local db_name="$(docker ps  | grep stevetags_database | cut -f 1 -d ' ')"
  docker run --rm --name psql -it -e PGPASSWORD --link "$db_name:postgres" \
    postgres:9.4.1 /bin/bash -c \
    'exec psql -h "$POSTGRES_PORT_5432_TCP_ADDR" -p "$POSTGRES_PORT_5432_TCP_PORT" -U postgres'
}

main "$@"
