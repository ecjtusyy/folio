#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

dc() { docker compose "$@"; }

if [ ! -f .env ]; then
  cp .env.example .env
  echo "[up.sh] Copied .env.example -> .env"
fi

set -a; source .env; set +a

mkdir -p "${APP_DATA_DIR}" "${APP_TMP_DIR}" "${APP_LOG_DIR}"
mkdir -p "${APP_DATA_DIR}/postgres" "${APP_DATA_DIR}/minio" "${APP_DATA_DIR}/onlyoffice"
mkdir -p "${CACHE_DIR}/pip" "${CACHE_DIR}/npm"

dc --env-file .env -f docker-compose.yml up -d --build
echo "[up.sh] Started."
