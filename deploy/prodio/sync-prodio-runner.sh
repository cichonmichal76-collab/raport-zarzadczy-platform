#!/bin/sh
set -eu

APP_DIR="${APP_DIR:-/opt/raport_zarzadczy_platform}"

cd "$APP_DIR"

STATE="$(docker compose exec -T web python manage.py prodio_sync_control state --format shell)"
eval "$STATE"

if [ "${PRODIO_SYNC_ENABLED:-0}" != "1" ] && [ "${PRODIO_SYNC_HAS_FORCED_RUN_PENDING:-0}" != "1" ]; then
  exit 0
fi

if [ "${PRODIO_SYNC_DUE:-0}" != "1" ] && [ "${PRODIO_SYNC_HAS_FORCED_RUN_PENDING:-0}" != "1" ]; then
  exit 0
fi

docker compose exec -T web python manage.py prodio_sync_control start

if "$APP_DIR/deploy/prodio/sync-prodio.sh"; then
  docker compose exec -T web python manage.py prodio_sync_control finish --status success
else
  status="$?"
  docker compose exec -T web python manage.py prodio_sync_control finish --status error --message "sync-prodio.sh exit $status" || true
  exit "$status"
fi
