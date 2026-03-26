#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing $1"; exit 1; }; }

need docker
need curl
need jq
need base64
need sha256sum
need unzip
docker compose version >/dev/null 2>&1 || { echo "docker compose missing"; exit 1; }

[ -f .env ] || cp .env.example .env
set -a; source .env; set +a

mkdir -p "${APP_DATA_DIR}" "${APP_TMP_DIR}" "${APP_LOG_DIR}"
mkdir -p "${CACHE_DIR}/pip" "${CACHE_DIR}/npm"

bash ./up.sh

PORT="${CADDY_HTTP_PORT:-80}"
BASE="http://localhost"
[ "$PORT" != "80" ] && BASE="http://localhost:${PORT}"

wait_http() {
  local url="$1"
  local tries=60
  for i in $(seq 1 $tries); do
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
    if [ "$code" = "200" ] || [ "$code" = "301" ] || [ "$code" = "302" ]; then
      echo "[verify] OK $url ($code)"
      return 0
    fi
    sleep 2
  done
  echo "[verify] FAIL $url"
  exit 1
}

wait_http "${BASE}/"
wait_http "${BASE}/api/health"
# onlyoffice via caddy
for i in $(seq 1 60); do
  txt="$(curl -s "${BASE}/onlyoffice/healthcheck" | tr -d '\r\n' || true)"
  if [ "$txt" = "true" ] || [ "$txt" = "True" ]; then
    echo "[verify] OK onlyoffice healthcheck"
    break
  fi
  sleep 2
  [ "$i" = "60" ] && { echo "[verify] FAIL onlyoffice healthcheck"; exit 1; }
done

bash ./verify_m1.sh
bash ./verify_m2.sh
bash ./verify_m3.sh

echo "[verify] ALL PASS"
