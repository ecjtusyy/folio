#!/usr/bin/env bash
set -euo pipefail

echo "[devcontainer] Preparing environment (python + node)..."

PROJECT_ROOT="/workspaces/folio"
cd "$PROJECT_ROOT"

# Ensure basic tools
sudo apt-get update -y >/dev/null
sudo apt-get install -y --no-install-recommends curl jq unzip ca-certificates >/dev/null

# Ensure app data directories exist
mkdir -p /home/codespace/.local/share/folio/tmp
mkdir -p /home/codespace/.local/share/folio/logs

# Python deps
if [ -f server/requirements.txt ]; then
  python -m pip install --upgrade pip >/dev/null
  pip install -r server/requirements.txt >/dev/null
  echo "[devcontainer] Python deps installed."
fi

# Node deps
if [ -f package.json ]; then
  if [ -f package-lock.json ]; then
    npm ci --no-audit --no-fund
  else
    npm install --no-audit --no-fund
  fi
  echo "[devcontainer] Node deps installed."
fi

echo "[devcontainer] Done."
echo "[devcontainer] Useful commands:"
echo "  - bash deploy/up.sh"
echo "  - bash deploy/verify_all.sh"