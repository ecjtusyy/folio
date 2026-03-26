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

dc() { docker compose "$@"; }
must_in() { [[ " $2 " == *" $1 "* ]] || { echo "Expected one of: $2 but got: $1"; exit 1; }; }

json_login="$(jq -n --arg u "${ADMIN_USERNAME}" --arg p "${ADMIN_PASSWORD}" '{username:$u,password:$p}')"

echo "[M3] login"
c=$(curl -s -o /dev/null -w "%{http_code}" -c "$COOKIE" -H 'Content-Type: application/json' -d "$json_login" "${BASE}/api/auth/login")
must_in "$c" "200"

# ensure pypdf exists in server container (for PDF page counting)
echo "[M3] check pypdf in server container"
dc exec -T server python -c "import pypdf; print('pypdf_ok')" >/dev/null

echo "[M3] import md(zip) private (with local assets)"
mdp=$(curl -s -b "$COOKIE" \
  -F "file=@${TD}/sample_md_with_assets.zip;type=application/zip" \
  -F "visibility=private" \
  -F "title=mdzip-private" \
  "${BASE}/api/imports")
mdpid=$(echo "$mdp" | jq -r '.id'); test -n "$mdpid"

# private access control
cna=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/api/library/${mdpid}")
must_in "$cna" "401 403"

# extract rewritten image url from content_md
img_url=$(echo "$mdp" | jq -r '.content_md' | grep -oE '/api/files/[0-9a-fA-F-]+/download' | head -n 1 || true)
test -n "$img_url"

echo "[M3] md(zip) image should require auth when private"
cimg_unauth=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}${img_url}")
must_in "$cimg_unauth" "401 403"

cimg_auth=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE" "${BASE}${img_url}")
must_in "$cimg_auth" "200"

echo "[M3] md(zip) switch to public and verify unauth can read"
json_pub="$(jq -n --arg v "public" '{visibility:$v}')"
curl -s -b "$COOKIE" -H 'Content-Type: application/json' -d "$json_pub" -X PUT "${BASE}/api/imports/${mdpid}" >/dev/null

cpub=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/api/library/${mdpid}")
must_in "$cpub" "200"

cimg_pub=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}${img_url}")
must_in "$cimg_pub" "200"

echo "[M3] import tex(zip) private (multipage)"
texr=$(curl -s -b "$COOKIE" \
  -F "file=@${TD}/sample_tex_multipage.zip;type=application/zip" \
  -F "visibility=private" \
  -F "title=tex-multipage-private" \
  "${BASE}/api/imports")
texid=$(echo "$texr" | jq -r '.id'); test -n "$texid"
pdfid=$(echo "$texr" | jq -r '.rendered_file_id'); test -n "$pdfid"

# private access control
cna=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/api/library/${texid}")
must_in "$cna" "401 403"

cpdf_unauth=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/api/files/${pdfid}/download")
must_in "$cpdf_unauth" "401 403"

echo "[M3] download compiled pdf (auth) and assert pages>=2"
curl -s -b "$COOKIE" "${BASE}/api/files/${pdfid}/download" | \
  dc exec -T server python - <<'PY'
import io, sys
from pypdf import PdfReader
data = sys.stdin.buffer.read()
r = PdfReader(io.BytesIO(data))
pages = len(r.pages)
print("pages=", pages)
assert pages >= 2, f"expected >=2 pages, got {pages}"
PY

echo "[M3] viewer route should be PDF.js viewer (200 + marker)"
cview=$(curl -s -o /dev/null -w "%{http_code}" -b "$COOKIE" "${BASE}/viewer/pdf/${pdfid}")
must_in "$cview" "200"
curl -s -b "$COOKIE" "${BASE}/viewer/pdf/${pdfid}" | grep -q "/pdfjs/web/viewer.html?file="

echo "[M3] switch tex import to public and verify unauth can read pdf"
curl -s -b "$COOKIE" -H 'Content-Type: application/json' -d "$json_pub" -X PUT "${BASE}/api/imports/${texid}" >/dev/null

cpub=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/api/library/${texid}")
must_in "$cpub" "200"

hdr="$(curl -s -I "${BASE}/api/files/${pdfid}/download" | tr -d '\r')"
echo "$hdr" | grep -qi "200"
echo "$hdr" | grep -qi "content-type: application/pdf"

echo "[M3] import docx (onlyoffice internal fetch)"
docx=$(curl -s -b "$COOKIE" \
  -F "file=@${TD}/sample.docx;type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
  -F "visibility=private" \
  -F "title=docx-private" \
  "${BASE}/api/imports")
docx_file_id=$(echo "$docx" | jq -r '.source_file_id'); test -n "$docx_file_id"

# get internal document.url for onlyoffice to fetch
docurl=$(curl -s -b "$COOKIE" "${BASE}/api/onlyoffice/document-url/${docx_file_id}" | jq -r '.document_url')
test -n "$docurl"

echo "[M3] onlyoffice container should curl document.url 200"
# docurl is internal (http://server:8000/...) so must be executed in onlyoffice container
dc exec -T onlyoffice curl -s -I "$docurl" | tr -d '\r' | grep -q "200"

echo "[M3] ok"
