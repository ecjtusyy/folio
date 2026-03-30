from __future__ import annotations
import os, uuid
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from ..auth import create_file_token, get_current_admin, verify_file_token
from ..config import settings
from ..db import get_db
from ..models import FileObject
from ..storage import head_object, stream_object

router=APIRouter(prefix="/api/onlyoffice", tags=["onlyoffice"])

def _auth(request: Request, fid: str, scope: str):
    if scope=="public":
        return
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

@router.get("/document-url/{file_id}")
def document_url(file_id: str, request: Request, db: Session=Depends(get_db)):
    try: uid=uuid.UUID(file_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    fo=db.get(FileObject, uid)
    if not fo: raise HTTPException(status_code=404, detail="not_found")
    _auth(request, file_id, fo.owner_scope)
    ttl=int(settings.file_token_ttl_seconds)
    tok=create_file_token(file_id, ttl)
    url=f"{settings.internal_server_base_url}/api/onlyoffice/doc/{file_id}?token={quote(tok)}"
    return {"file_id": file_id, "document_url": url, "expires_in": ttl}

@router.head("/doc/{file_id}")
def head(file_id: str, request: Request, db: Session=Depends(get_db)):
    try: uid=uuid.UUID(file_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    fo=db.get(FileObject, uid)
    if not fo: raise HTTPException(status_code=404, detail="not_found")
    _auth(request, file_id, fo.owner_scope)
    meta=head_object(fo.object_key)
    return Response(status_code=200, headers={"Content-Type": fo.mime, "Content-Length": str(meta.get("ContentLength",""))})

@router.get("/doc/{file_id}")
def get_doc(file_id: str, request: Request, db: Session=Depends(get_db)):
    try: uid=uuid.UUID(file_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    fo=db.get(FileObject, uid)
    if not fo: raise HTTPException(status_code=404, detail="not_found")
    _auth(request, file_id, fo.owner_scope)
    it, meta=stream_object(fo.object_key)
    headers={"Content-Type": fo.mime, "Content-Disposition": f'inline; filename="{os.path.basename(fo.object_key)}"'}
    if meta.get("content_length") is not None:
        headers["Content-Length"]=str(meta["content_length"])
    return StreamingResponse(it, headers=headers, media_type=fo.mime)

@router.post("/callback")
async def callback(request: Request):
    _=await request.body()
    return {"error": 0}
