#!/bin/sh
set -eu

APP_DIR="${APP_DIR:-/opt/raport_zarzadczy_platform}"
OUTPUT_JSON="${OUTPUT_JSON:-/root/prodio_orders.json}"

cd "$APP_DIR"

PRODIO_BASE_URL="$(grep -m1 '^PRODIO_BASE_URL=' .env | cut -d= -f2-)"
PRODIO_API_TOKEN="$(grep '^PRODIO_API_TOKEN=' .env | tail -1 | cut -d= -f2-)"

if [ -z "$PRODIO_BASE_URL" ] || [ -z "$PRODIO_API_TOKEN" ]; then
  echo "Brak PRODIO_BASE_URL albo PRODIO_API_TOKEN w $APP_DIR/.env" >&2
  exit 1
fi

fetch_prodio() {
  endpoint="$1"
  output="$2"
  shift 2

  curl -fsS \
    --get \
    --data-urlencode "api_token=$PRODIO_API_TOKEN" \
    "$@" \
    "$PRODIO_BASE_URL/api/$endpoint" \
    -o "$output"
}

fetch_prodio orders "$OUTPUT_JSON"

docker compose exec -T web python manage.py sync_prodio_orders --input-json - < "$OUTPUT_JSON"

for resource in products clients; do
  resource_json="/root/prodio_${resource}.json"
  fetch_prodio "$resource" "$resource_json"
  docker compose exec -T web python manage.py sync_prodio_raw "$resource" --input-json - < "$resource_json"
done

tasks_json="/root/prodio_order_machines.json"
if fetch_prodio order-machines "$tasks_json" --data-urlencode "s=" --data-urlencode "status=1,2,4"; then
  docker compose exec -T web python manage.py sync_prodio_raw order-machines --input-json - < "$tasks_json"
fi
