#!/bin/sh
set -e
cd "$(dirname "$0")/../.."
docker compose --profile backup run --rm backup
