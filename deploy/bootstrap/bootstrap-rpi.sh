#!/bin/sh
set -e

APP_DIR="/opt/raport_zarzadczy_platform"

echo "[1/6] Aktualizacja systemu"
sudo apt update && sudo apt upgrade -y

echo "[2/6] Instalacja Docker"
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"

echo "[3/6] Instalacja pluginu compose"
sudo apt install -y docker-compose-plugin openssl

echo "[4/6] Kopiowanie aplikacji do ${APP_DIR}"
sudo mkdir -p "${APP_DIR}"
sudo cp -R . "${APP_DIR}"
sudo chown -R "$USER":"$USER" "${APP_DIR}"

echo "[5/6] Generowanie certyfikatu self-signed"
cd "${APP_DIR}"
chmod +x deploy/certs/generate-selfsigned.sh
./deploy/certs/generate-selfsigned.sh

echo "[6/6] Uruchomienie stacka"
docker compose up --build -d

echo "Zaloguj się ponownie do shell, jeśli grupa docker jeszcze nie działa."
