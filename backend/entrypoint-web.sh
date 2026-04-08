#!/bin/sh
set -e

python - <<'PY'
import os
import socket
import time

targets = [
    (os.getenv("POSTGRES_HOST", "db"), int(os.getenv("POSTGRES_PORT", "5432")), "postgres"),
    ("redis", 6379, "redis"),
]

for host, port, name in targets:
    for attempt in range(60):
        try:
            with socket.create_connection((host, port), timeout=2):
                print(f"{name} ready on {host}:{port}")
                break
        except OSError:
            time.sleep(2)
    else:
        raise SystemExit(f"{name} not reachable on {host}:{port}")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 2 \
  --threads 2 \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
