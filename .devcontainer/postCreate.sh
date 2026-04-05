#!/usr/bin/env bash
set -euo pipefail

echo "[devcontainer] lightweight bootstrap..."

mkdir -p /home/codespace/.local/share/folio/tmp
mkdir -p /home/codespace/.local/share/folio/logs

cd /workspaces/folio

if [ ! -f deploy/.env ]; then
  cp deploy/.env.example deploy/.env
  echo "[devcontainer] copied deploy/.env.example -> deploy/.env"
fi

echo "[devcontainer] ready"
echo "next: bash deploy/up.sh"