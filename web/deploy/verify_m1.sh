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

code() { curl -s -o /dev/null -w "%{http_code}" -X "$1" "$2" "${@:3}"; }
must_in() { [[ " $2 " == *" $1 "* ]] || { echo "Expected $2 got $1"; exit 1; }; }

echo "[M1] login"
c=$(curl -s -o /dev/null -w "%{http_code}" -c "$COOKIE" -H 'Content-Type: application/json'   -d "{"username":"${ADMIN_USERNAME}","password":"${ADMIN_PASSWORD}"}"   "${BASE}/api/auth/login")
must_in "$c" "200"

me=$(curl -s -b "$COOKIE" "${BASE}/api/auth/me")
echo "$me" | jq -e '.authenticated==true' >/dev/null

echo "[M1] create note"
n=$(curl -s -b "$COOKIE" -H 'Content-Type: application/json'   -d '{"title":"m1","content_md":"Inline $E=mc^2$\n\n$$\\int_0^1 x^2 dx=1/3$$\n"}'   "${BASE}/api/notes")
id=$(echo "$n" | jq -r '.id')
test -n "$id"

lst=$(curl -s -b "$COOKIE" "${BASE}/api/notes")
echo "$lst" | jq -e --arg id "$id" 'map(.id)|index($id)!=null' >/dev/null

echo "[M1] update"
u=$(curl -s -b "$COOKIE" -X PUT -H 'Content-Type: application/json'   -d '{"title":"m1u","content_md":"$$\\begin{align}a&=b\\\\c&=d\\end{align}$$"}'   "${BASE}/api/notes/${id}")
echo "$u" | jq -e '.title=="m1u"' >/dev/null

echo "[M1] upload private image"
up=$(curl -s -b "$COOKIE" -F "file=@${TD}/sample.png;type=image/png" -F "owner_scope=private" -F "kind=image"   "${BASE}/api/files/upload")
fid=$(echo "$up" | jq -r '.id')
url=$(echo "$up" | jq -r '.download_url')
test -n "$fid"; test -n "$url"

c0=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}${url}")
must_in "$c0" "401 403"

hdr=$(curl -s -D - -o /dev/null -b "$COOKIE" "${BASE}${url}")
echo "$hdr" | head -n 1 | grep -q "200"
echo "$hdr" | tr -d '\r' | grep -i -q '^content-type: *image/png'

echo "[M1] delete note"
c2=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE" -X DELETE "${BASE}/api/notes/${id}")
must_in "$c2" "200"

echo "[M1] PASS"
