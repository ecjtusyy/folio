#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "[1] dynamic routes" && find app -path '*/[*]*/*.tsx' | sort
echo "[2] generateStaticParams" && grep -RIn 'generateStaticParams' app
echo "[3] forbidden dynamic/runtime items" && if grep -RInE 'force-dynamic|cookies\(|headers\(|draftMode\(|/api/|server:8000|revalidate\s*=\s*0|localStorage|window\.|document\.' app lib components; then exit 1; else echo 'No forbidden runtime dependency found'; fi
echo "[4] navigation cleanup" && if grep -RInE 'Login|Admin|Imports|/login|/admin|/imports|/notes' app components; then exit 1; else echo 'Navigation clean'; fi
echo "[5] required pages" && for p in about papers projects cv contact; do test -f "app/$p/page.tsx"; done && echo 'Required pages present'
