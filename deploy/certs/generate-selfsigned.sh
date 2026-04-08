#!/bin/sh
set -e

CERT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
openssl req -x509 -nodes -days 825 -newkey rsa:2048 \
  -keyout "${CERT_DIR}/selfsigned.key" \
  -out "${CERT_DIR}/selfsigned.crt" \
  -subj "/C=PL/ST=Local/L=Local/O=RaportZarzadczy/CN=raspberrypi.local"

echo "Wygenerowano:"
echo "  ${CERT_DIR}/selfsigned.crt"
echo "  ${CERT_DIR}/selfsigned.key"
