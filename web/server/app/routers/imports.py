from __future__ import annotations

import hashlib
import io
import mimetypes
import os
import posixpath
import re
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_admin
from ..config import settings
from ..db import get_db
from ..models import FileObject, ImportAsset
from ..storage import put_bytes
from ..tex import TexCompileError, compile_tex_zip

router = APIRouter(prefix="/api/imports", tags=["imports"])
router_public = APIRouter(prefix="/api/public/imports", tags=["public-imports"])
router_library = APIRouter(prefix="/api/library", tags=["library"])

INLINE_IMG_RE = re.compile(r"(!\[[^\]]*\]\()([^\)]+)(\))")
REF_IMG_RE = re.compile(r"!\[([^\]]*)\]\[([^\]]*)\]")
REF_DEF_RE = re.compile(r"^\s*\[([^\]]+)\]:\s*(\S+)(.*)$", re.M)
HTML_IMG_RE = re.compile(r"(<img\b[^>]*?\bsrc=)([\"\'])([^\"\']+)(\2)", re.I)

def _out(a: ImportAsset):
    return {
        "id": str(a.id),
        "type": a.type,
        "visibility": a.visibility,
        "title": a.title,
        "source_file_id": str(a.source_file_id),
        "rendered_file_id": str(a.rendered_file_id) if a.rendered_file_id else None,
        "asset_file_ids": a.asset_file_ids or [],
        "content_md": a.content_md,
        "created_at": a.created_at,
    }

def _store(db: Session, data: bytes, filename: str, owner_scope: str, kind: str, mime: str) -> FileObject:
    sha = hashlib.sha256(data).hexdigest()
    key = f"imports/{uuid.uuid4().hex}_{os.path.basename(filename)}"
    put_bytes(data, key, mime)
    fo = FileObject(owner_scope=owner_scope, kind=kind, bucket=settings.minio_bucket, object_key=key, mime=mime, size=len(data), sha256=sha)
    db.add(fo); db.commit(); db.refresh(fo)
    return fo

def _is_remote_url(u: str) -> bool:
    u = u.strip()
    return u.startswith("http://") or u.startswith("https://") or u.startswith("data:") or u.startswith("//")

def _is_local_ref(u: str) -> bool:
    u = u.strip()
    if not u:
        return False
    if _is_remote_url(u):
        return False
    if u.startswith("/"):
        return False
    # other schemes like mailto:
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", u):
        return False
    return True

def _parse_inline_target(raw: str) -> tuple[str, str]:
    """return (url, rest) where rest includes optional title."""
    s = raw.strip()
    if s.startswith("<") and ">" in s:
        end = s.find(">")
        url = s[1:end]
        rest = s[end+1:].strip()
        return url, rest
    parts = s.split()
    if not parts:
        return "", ""
    url = parts[0]
    rest = " ".join(parts[1:]).strip()
    return url, rest

def _select_main_md(zip_names: list[str]) -> str:
    mds = [n for n in zip_names if n.lower().endswith(".md") and not n.endswith("/")]
    # prefer main.md (anywhere)
    for n in mds:
        if posixpath.basename(n).lower() == "main.md":
            return n
    if len(mds) == 1:
        return mds[0]
    if len(mds) == 0:
        raise HTTPException(status_code=400, detail={"error":"no_md_found_in_zip"})
    raise HTTPException(status_code=400, detail={"error":"multiple_md_found", "candidates": sorted(mds)})

def _resolve_zip_path(md_path_in_zip: str, ref: str) -> str:
    """resolve relative ref -> normalized zip path (posix)."""
    ref = ref.strip()
    split = urlsplit(ref)
    p = split.path or ""
    p = p.replace("\\", "/")
    base_dir = posixpath.dirname(md_path_in_zip)
    joined = posixpath.normpath(posixpath.join(base_dir, p))
    if joined.startswith("..") or joined.startswith("/"):
        raise HTTPException(status_code=400, detail={"error":"invalid_relative_path", "path": ref})
    return joined

def _collect_local_refs(md_text: str) -> tuple[set[str], dict[str,str]]:
    """return (inline_and_html_urls, ref_defs)"""
    urls: set[str] = set()
    # inline images
    for m in INLINE_IMG_RE.finditer(md_text):
        raw = m.group(2)
        url, _rest = _parse_inline_target(raw)
        if _is_local_ref(url):
            urls.add(url)
    # html images
    for m in HTML_IMG_RE.finditer(md_text):
        url = m.group(3).strip()
        if _is_local_ref(url):
            urls.add(url)

    # reference-style images: collect used keys then resolve definitions
    used_keys: set[str] = set()
    for m in REF_IMG_RE.finditer(md_text):
        alt = m.group(1).strip()
        key = m.group(2).strip() or alt
        if key:
            used_keys.add(key)

    ref_defs: dict[str,str] = {}
    for m in REF_DEF_RE.finditer(md_text):
        key = m.group(1).strip()
        url = m.group(2).strip()
        if url.startswith("<") and url.endswith(">"):
            url = url[1:-1]
        ref_defs[key] = url

    for k in used_keys:
        u = ref_defs.get(k)
        if u and _is_local_ref(u):
            urls.add(u)

    return urls, ref_defs

def _rewrite_md_with_assets(db: Session, job_dir: Path, md_path_in_zip: str, md_text: str, visibility: str) -> tuple[str, list[str]]:
    local_urls, _ref_defs = _collect_local_refs(md_text)

    # resolve and validate first (avoid partial uploads)
    resolved_map: dict[str, list[str]] = {}
    missing: list[str] = []
    for u in sorted(local_urls):
        resolved = _resolve_zip_path(md_path_in_zip, u)
        full = job_dir / resolved
        if not full.exists() or not full.is_file():
            missing.append(u)
            continue
        resolved_map.setdefault(resolved, []).append(u)

    if missing:
        raise HTTPException(status_code=400, detail={"error":"missing_resources", "missing": missing})

    resolved_to_url: dict[str, str] = {}
    asset_ids: list[str] = []

    for resolved in sorted(resolved_map.keys()):
        full = job_dir / resolved
        b = full.read_bytes()
        mime, _ = mimetypes.guess_type(full.name)
        mime = mime or "application/octet-stream"
        fo = _store(db, b, full.name, visibility, "import_md_asset", mime)
        asset_ids.append(str(fo.id))
        resolved_to_url[resolved] = f"/api/files/{fo.id}/download"

    # helper: given url, return rewritten or None
    def rewrite_url(url: str) -> str | None:
        if not _is_local_ref(url):
            return None
        resolved = _resolve_zip_path(md_path_in_zip, url)
        return resolved_to_url.get(resolved)

    # rewrite inline images
    def inline_sub(m: re.Match) -> str:
        prefix, raw, suffix = m.group(1), m.group(2), m.group(3)
        url, rest = _parse_inline_target(raw)
        newu = rewrite_url(url)
        if not newu:
            return m.group(0)
        new_raw = newu + ("" if rest == "" else " " + rest)
        return prefix + new_raw + suffix

    md_text2 = INLINE_IMG_RE.sub(inline_sub, md_text)

    # rewrite html images
    def html_sub(m: re.Match) -> str:
        pre, q, url, q2 = m.group(1), m.group(2), m.group(3), m.group(4)
        newu = rewrite_url(url)
        if not newu:
            return m.group(0)
        return f"{pre}{q}{newu}{q2}"

    md_text2 = HTML_IMG_RE.sub(html_sub, md_text2)

    # rewrite reference definitions (only when value is local)
    def def_sub(m: re.Match) -> str:
        key = m.group(1).strip()
        url = m.group(2).strip()
        rest = m.group(3) or ""
        newu = rewrite_url(url)
        if not newu:
            return m.group(0)
        return f"[{key}]: {newu}{rest}"

    md_text2 = REF_DEF_RE.sub(def_sub, md_text2)

    return md_text2, asset_ids

def _md_has_local_asset_refs(md_text: str) -> bool:
    urls, _ = _collect_local_refs(md_text)
    return len(urls) > 0

@router.post("")
def create(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
    file: UploadFile = File(...),
    visibility: str = Form("private"),
    title: str | None = Form(None),
    main_tex: str | None = Form(None),
):
    if visibility not in ("private", "public"):
        raise HTTPException(status_code=400, detail="invalid_visibility")
    name = file.filename or "upload"
    data = file.file.read()
    ext = os.path.splitext(name.lower())[1]

    if ext == ".md":
        md = data.decode("utf-8", errors="replace")
        if _md_has_local_asset_refs(md):
            raise HTTPException(status_code=400, detail={"error":"md_contains_relative_assets", "hint":"upload a .zip (md + assets) for faithful import"})
        fo = _store(db, data, name, visibility, "import_md", "text/markdown")
        a = ImportAsset(type="md", visibility=visibility, source_file_id=fo.id, rendered_file_id=None, asset_file_ids=[], title=title or name, content_md=md)
        db.add(a); db.commit(); db.refresh(a)
        return _out(a)

    if ext == ".docx":
        fo = _store(db, data, name, visibility, "import_docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        a = ImportAsset(type="docx", visibility=visibility, source_file_id=fo.id, rendered_file_id=None, asset_file_ids=[], title=title or name, content_md=None)
        db.add(a); db.commit(); db.refresh(a)
        return _out(a)

    if ext == ".zip":
        # inspect zip content to decide tex vs md+assets
        try:
            with zipfile.ZipFile(io.BytesIO(data), "r") as zf:  # type: ignore
                names = zf.namelist()
        except Exception:
            raise HTTPException(status_code=400, detail={"error":"invalid_zip"})

        has_tex = any(n.lower().endswith(".tex") for n in names if not n.endswith("/"))
        has_md = any(n.lower().endswith(".md") for n in names if not n.endswith("/"))

        if has_tex:
            zipfo = _store(db, data, name, visibility, "import_tex_zip", "application/zip")
            try:
                pdf = compile_tex_zip(data, main_tex=main_tex)
            except TexCompileError as e:
                detail = {"error": str(e), "tail": e.tail}
                if getattr(e, "candidates", None):
                    detail["candidates"] = e.candidates
                    detail["hint"] = "pass form field main_tex=<path/to/file.tex> to choose"
                raise HTTPException(status_code=400, detail=detail)
            pdffo = _store(db, pdf, "compiled.pdf", visibility, "import_tex_pdf", "application/pdf")
            a = ImportAsset(type="tex", visibility=visibility, source_file_id=zipfo.id, rendered_file_id=pdffo.id, asset_file_ids=[], title=title or name, content_md=None)
            db.add(a); db.commit(); db.refresh(a)
            return _out(a)

        if has_md:
            zipfo = _store(db, data, name, visibility, "import_md_zip", "application/zip")
            # extract to tmp dir
            root_tmp = os.path.join(settings.app_tmp_dir, "mdjobs")
            os.makedirs(root_tmp, exist_ok=True)
            job = tempfile.mkdtemp(prefix="job_", dir=root_tmp)
            try:
                zp = os.path.join(job, "src.zip")
                with open(zp, "wb") as f:
                    f.write(data)
                with zipfile.ZipFile(zp, "r") as zf:
                    zf.extractall(job)
                    md_in_zip = _select_main_md(zf.namelist())
                md_abs = Path(job) / md_in_zip
                if not md_abs.exists():
                    # extracted paths may differ when zip has top folder, fallback: search by basename
                    cand = list(Path(job).rglob(posixpath.basename(md_in_zip)))
                    if len(cand) == 1:
                        md_abs = cand[0]
                        # recompute md_in_zip relative to job
                        md_in_zip = str(md_abs.relative_to(Path(job))).replace(os.sep, "/")
                    else:
                        raise HTTPException(status_code=400, detail={"error":"main_md_not_found_after_extract", "candidates": [str(p.relative_to(Path(job))) for p in cand]})
                md_text = md_abs.read_text(encoding="utf-8", errors="replace")

                rewritten_md, asset_ids = _rewrite_md_with_assets(db, Path(job), md_in_zip, md_text, visibility)
                a = ImportAsset(type="md", visibility=visibility, source_file_id=zipfo.id, rendered_file_id=None, asset_file_ids=asset_ids, title=title or posixpath.basename(md_in_zip), content_md=rewritten_md)
                db.add(a); db.commit(); db.refresh(a)
                return _out(a)
            finally:
                try:
                    shutil.rmtree(job)
                except Exception:
                    pass

        raise HTTPException(status_code=400, detail={"error":"zip_contains_no_tex_or_md"})

    raise HTTPException(status_code=400, detail="unsupported_file_type")

@router.get("")
def list_admin(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    items = db.execute(select(ImportAsset).order_by(ImportAsset.created_at.desc())).scalars().all()
    return [_out(a) for a in items]

@router.get("/{import_id}")
def get_admin(import_id: str, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    try:
        uid = uuid.UUID(import_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_id")
    a = db.get(ImportAsset, uid)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    return _out(a)

@router.put("/{import_id}")
def update(import_id: str, payload: dict, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    try:
        uid = uuid.UUID(import_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_id")
    a = db.get(ImportAsset, uid)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")

    if payload.get("title") is not None:
        a.title = str(payload["title"])

    if payload.get("visibility") is not None:
        v = payload["visibility"]
        if v not in ("private", "public"):
            raise HTTPException(status_code=400, detail="invalid_visibility")
        a.visibility = v

        # update all linked file objects
        for fid in [a.source_file_id, a.rendered_file_id]:
            if not fid:
                continue
            fo = db.get(FileObject, fid)
            if fo:
                fo.owner_scope = v
                db.add(fo)

        for fid_str in (a.asset_file_ids or []):
            try:
                fid = uuid.UUID(fid_str)
            except Exception:
                continue
            fo = db.get(FileObject, fid)
            if fo:
                fo.owner_scope = v
                db.add(fo)

    db.add(a); db.commit(); db.refresh(a)
    return _out(a)

@router.delete("/{import_id}")
def delete(import_id: str, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    try:
        uid = uuid.UUID(import_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_id")
    a = db.get(ImportAsset, uid)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    db.delete(a); db.commit()
    return {"ok": True}

@router_public.get("/{import_id}")
def public_get(import_id: str, db: Session = Depends(get_db)):
    try:
        uid = uuid.UUID(import_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_id")
    a = db.get(ImportAsset, uid)
    if not a or a.visibility != "public":
        raise HTTPException(status_code=404, detail="not_found")
    return _out(a)

@router_library.get("/{import_id}")
def library_get(import_id: str, request: Request, db: Session = Depends(get_db)):
    try:
        uid = uuid.UUID(import_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_id")
    a = db.get(ImportAsset, uid)
    if not a:
        raise HTTPException(status_code=404, detail="not_found")
    if a.visibility != "public":
        get_current_admin(request)
    return _out(a)
