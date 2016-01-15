#!/bin/bash
set -eo pipefail

source /envs/aws/bin/activate

main() {
  docker run --rm -it \
    -e PGPASSWORD=$(cat $HOME/PGPASSWORD) \
    --link stevetags-db:postgres \
    -v /tmp:/mnt \
    postgres:9.4.1 /bin/bash -c \
    'exec pg_dump -c --format=p -f /mnt/dump.sql -h "$POSTGRES_PORT_5432_TCP_ADDR" -p "$POSTGRES_PORT_5432_TCP_PORT" -U postgres'

  aws s3 cp /tmp/dump.sql s3://stevetags-db-backups/$(date +%Y-%m-%d).sql
}

main "$@"
