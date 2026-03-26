#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
set -a; source .env; set +a

PORT="${CADDY_HTTP_PORT:-80}"
BASE="http://localhost"
[ "$PORT" != "80" ] && BASE="http://localhost:${PORT}"

COOKIE="$(mktemp)"
trap 'rm -f "$COOKIE"' EXIT
TD="$(cd ../testdata && pwd)"

must_in() { [[ " $2 " == *" $1 "* ]] || { echo "Expected $2 got $1"; exit 1; }; }

echo "[M2] login"
c=$(curl -s -o /dev/null -w "%{http_code}" -c "$COOKIE" -H 'Content-Type: application/json'   -d "{"username":"${ADMIN_USERNAME}","password":"${ADMIN_PASSWORD}"}"   "${BASE}/api/auth/login")
must_in "$c" "200"

echo "[M2] upload public image"
up=$(curl -s -b "$COOKIE" -F "file=@${TD}/sample.png;type=image/png" -F "owner_scope=public" -F "kind=image"   "${BASE}/api/files/upload")
imgurl=$(echo "$up" | jq -r '.download_url')

slug="m2-$(date +%s)-$RANDOM"
echo "[M2] create draft post"
p=$(curl -s -b "$COOKIE" -H 'Content-Type: application/json'   -d "{"title":"Draft","slug":"${slug}","summary":"s","content_md":"# Draft\nMath $E=mc^2$\nImage: ![](${imgurl})\n","status":"draft","tags":["m2"]}"   "${BASE}/api/posts")
pid=$(echo "$p" | jq -r '.id'); test -n "$pid"

lst=$(curl -s "${BASE}/api/public/posts")
echo "$lst" | jq -e --arg s "$slug" 'map(.slug)|index($s)==null' >/dev/null

c404=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/api/public/posts/${slug}")
must_in "$c404" "404"

echo "[M2] publish"
pub=$(curl -s -b "$COOKIE" -X POST "${BASE}/api/posts/${pid}/publish")
echo "$pub" | jq -e '.status=="published"' >/dev/null

lst2=$(curl -s "${BASE}/api/public/posts")
echo "$lst2" | jq -e --arg s "$slug" 'map(.slug)|index($s)!=null' >/dev/null

c200=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/api/public/posts/${slug}")
must_in "$c200" "200"

codep=$(curl -s -o /dev/null -w "%{http_code}" -I "${BASE}/posts/${slug}")
must_in "$codep" "200 301 302"

imgc=$(curl -s -o /dev/null -w "%{http_code}" -I "${BASE}${imgurl}")
must_in "$imgc" "200"

echo "[M2] PASS"
