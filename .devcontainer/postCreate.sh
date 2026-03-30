#!/usr/bin/env bash
set -euo pipefail

echo "[devcontainer] Preparing environment (python + node)..."
cd /workspace/project

# Ensure basic tools
sudo apt-get update -y >/dev/null
sudo apt-get install -y --no-install-recommends curl jq unzip ca-certificates >/dev/null

# Python deps (server)
if [ -f server/requirements.txt ]; then
  python -m pip install --upgrade pip >/dev/null
  pip install -r server/requirements.txt >/dev/null
  echo "[devcontainer] Python deps installed."
fi

# Node deps (web)
if [ -f web/package.json ]; then
  cd web
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
