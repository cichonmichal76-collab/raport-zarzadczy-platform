#!/bin/sh
set -e

STAMP="$(date +%Y%m%d_%H%M%S)"
TARGET_DIR="${BACKUP_DIR:-/backups}"
mkdir -p "$TARGET_DIR"

pg_dump \
  -h "${POSTGRES_HOST:-db}" \
  -U "${POSTGRES_USER:-raport}" \
  -d "${POSTGRES_DB:-raport}" \
  -Fc \
  -f "${TARGET_DIR}/raport_${STAMP}.dump"

find "$TARGET_DIR" -type f -name "*.dump" -mtime +"${BACKUP_RETENTION_DAYS:-7}" -delete
