from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..auth import get_current_admin
from ..db import get_db
from ..models import Note

router=APIRouter(prefix="/api/notes", tags=["notes"])

def out(n: Note):
    return {"id": str(n.id), "title": n.title, "content_md": n.content_md, "created_at": n.created_at, "updated_at": n.updated_at}

@router.get("")
def list_notes(db: Session=Depends(get_db), admin=Depends(get_current_admin)):
    notes=db.execute(select(Note).order_by(Note.updated_at.desc())).scalars().all()
    return [out(n) for n in notes]

@router.post("")
def create(payload: dict, db: Session=Depends(get_db), admin=Depends(get_current_admin)):
    title=str(payload.get("title","")).strip()
    if not title:
        raise HTTPException(status_code=400, detail="title_required")
    n=Note(title=title, content_md=str(payload.get("content_md","")))
    db.add(n); db.commit(); db.refresh(n)
    return out(n)

@router.get("/{note_id}")
def get(note_id: str, db: Session=Depends(get_db), admin=Depends(get_current_admin)):
    try: uid=uuid.UUID(note_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    n=db.get(Note, uid)
    if not n: raise HTTPException(status_code=404, detail="not_found")
    return out(n)

@router.put("/{note_id}")
def update(note_id: str, payload: dict, db: Session=Depends(get_db), admin=Depends(get_current_admin)):
    try: uid=uuid.UUID(note_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    n=db.get(Note, uid)
    if not n: raise HTTPException(status_code=404, detail="not_found")
    if "title" in payload and payload["title"] is not None:
        t=str(payload["title"]).strip()
        if not t: raise HTTPException(status_code=400, detail="title_required")
        n.title=t
    if "content_md" in payload and payload["content_md"] is not None:
        n.content_md=str(payload["content_md"])
    db.add(n); db.commit(); db.refresh(n)
    return out(n)

@router.delete("/{note_id}")
def delete(note_id: str, db: Session=Depends(get_db), admin=Depends(get_current_admin)):
    try: uid=uuid.UUID(note_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    n=db.get(Note, uid)
    if not n: raise HTTPException(status_code=404, detail="not_found")
    db.delete(n); db.commit()
    return {"ok": True}
