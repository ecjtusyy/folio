#!/usr/bin/env bash
set -euo pipefail

cd /workspaces/folio

mkdir -p /root/.local/share/folio/tmp
mkdir -p /root/.local/share/folio/logs

if [ ! -f deploy/.env ]; then
  cp deploy/.env.example deploy/.env
  echo "[postCreate] copied deploy/.env.example -> deploy/.env"
fi

chmod +x deploy/*.sh || true

echo "[postCreate] ready"
echo "Next:"
echo "  bash deploy/up.sh"
echo "  bash deploy/verify_all.sh"