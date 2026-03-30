from __future__ import annotations
import hashlib, mimetypes, os, uuid
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from ..auth import create_file_token, get_current_admin, verify_file_token
from ..config import settings
from ..db import get_db
from ..models import FileObject
from ..storage import put_bytes, stream_object, head_object

router=APIRouter(prefix="/api/files", tags=["files"])

def _download_url(fid: str) -> str:
    return f"/api/files/{fid}/download"

def _authorize_private(request: Request, fid: str):
    try:
        get_current_admin(request); return
    except Exception:
        pass
    tok=request.query_params.get("token")
    if tok:
        sub=verify_file_token(tok)
        if sub==fid:
            return
        raise HTTPException(status_code=403, detail="invalid_token")
    raise HTTPException(status_code=401, detail="not_authenticated")

@router.post("/upload")
def upload(request: Request, db: Session=Depends(get_db), admin=Depends(get_current_admin),
           file: UploadFile=File(...), owner_scope: str=Form("private"), kind: str=Form("image")):
    if owner_scope not in ("private","public"):
        raise HTTPException(status_code=400, detail="invalid_owner_scope")
    data=file.file.read()
    sha=hashlib.sha256(data).hexdigest()
    mime=file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    key=f"uploads/{uuid.uuid4().hex}_{os.path.basename(file.filename or 'file')}"
    put_bytes(data, key, mime)
    fo=FileObject(owner_scope=owner_scope, kind=kind, bucket=settings.minio_bucket, object_key=key, mime=mime, size=len(data), sha256=sha)
    db.add(fo); db.commit(); db.refresh(fo)
    return {"id": str(fo.id), "owner_scope": fo.owner_scope, "kind": fo.kind, "mime": fo.mime, "size": fo.size, "sha256": fo.sha256, "download_url": _download_url(str(fo.id))}

@router.post("/{file_id}/token")
def token(file_id: str, request: Request, db: Session=Depends(get_db), admin=Depends(get_current_admin), ttl_seconds: int|None=Form(None)):
    try: uid=uuid.UUID(file_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    fo=db.get(FileObject, uid)
    if not fo: raise HTTPException(status_code=404, detail="not_found")
    ttl=int(ttl_seconds or settings.file_token_ttl_seconds)
    tok=create_file_token(file_id, ttl)
    return {
        "id": file_id,
        "token": tok,
        "expires_in": ttl,
        "download_url_with_token": f"{_download_url(file_id)}?token={quote(tok)}",
        "internal_download_url_with_token": f"{settings.internal_server_base_url}{_download_url(file_id)}?token={quote(tok)}"
    }

@router.head("/{file_id}/download")
def head(file_id: str, request: Request, db: Session=Depends(get_db)):
    try: uid=uuid.UUID(file_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    fo=db.get(FileObject, uid)
    if not fo: raise HTTPException(status_code=404, detail="not_found")
    if fo.owner_scope!="public":
        _authorize_private(request, file_id)
    meta=head_object(fo.object_key)
    return Response(status_code=200, headers={"Content-Type": fo.mime, "Content-Length": str(meta.get("ContentLength", ""))})

@router.get("/{file_id}/download")
def download(file_id: str, request: Request, db: Session=Depends(get_db)):
    try: uid=uuid.UUID(file_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    fo=db.get(FileObject, uid)
    if not fo: raise HTTPException(status_code=404, detail="not_found")
    if fo.owner_scope!="public":
        _authorize_private(request, file_id)
    it, meta=stream_object(fo.object_key)
    headers={"Content-Type": fo.mime, "Content-Disposition": f'inline; filename="{os.path.basename(fo.object_key)}"'}
    if meta.get("content_length") is not None:
        headers["Content-Length"]=str(meta["content_length"])
    return StreamingResponse(it, headers=headers, media_type=fo.mime)
