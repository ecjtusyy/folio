from __future__ import annotations
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..auth import get_current_admin
from ..db import get_db
from ..models import Post

router_public=APIRouter(prefix="/api/public/posts", tags=["posts-public"])
router_admin=APIRouter(prefix="/api/posts", tags=["posts-admin"])

def to_public(p: Post):
    tags=p.tags if isinstance(p.tags, list) else (p.tags or None)
    return {"title": p.title, "slug": p.slug, "summary": p.summary, "content_md": p.content_md, "published_at": p.published_at, "tags": tags}

def to_admin(p: Post):
    d=to_public(p)
    d.update({"id": str(p.id), "status": p.status, "created_at": p.created_at, "updated_at": p.updated_at})
    return d

@router_public.get("")
def pub_list(db: Session=Depends(get_db)):
    ps=db.execute(select(Post).where(Post.status=="published").order_by(Post.published_at.desc())).scalars().all()
    return [to_public(p) for p in ps]

@router_public.get("/{slug}")
def pub_detail(slug: str, db: Session=Depends(get_db)):
    p=db.execute(select(Post).where(Post.slug==slug)).scalar_one_or_none()
    if not p or p.status!="published":
        raise HTTPException(status_code=404, detail="not_found")
    return to_public(p)

@router_admin.get("")
def admin_list(db: Session=Depends(get_db), admin=Depends(get_current_admin)):
    ps=db.execute(select(Post).order_by(Post.updated_at.desc())).scalars().all()
    return [to_admin(p) for p in ps]

@router_admin.post("")
def admin_create(payload: dict, db: Session=Depends(get_db), admin=Depends(get_current_admin)):
    status_=payload.get("status","draft")
    if status_ not in ("draft","published"):
        raise HTTPException(status_code=400, detail="invalid_status")
    title=str(payload.get("title","")).strip()
    slug=str(payload.get("slug","")).strip()
    if not title or not slug:
        raise HTTPException(status_code=400, detail="title_slug_required")
    p=Post(
        title=title, slug=slug, summary=payload.get("summary"),
        content_md=str(payload.get("content_md","")),
        status=status_,
        published_at=(datetime.now(timezone.utc) if status_=="published" else None),
        tags=payload.get("tags"),
    )
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="slug_conflict")
    db.refresh(p)
    return to_admin(p)

@router_admin.put("/{post_id}")
def admin_update(post_id: str, payload: dict, db: Session=Depends(get_db), admin=Depends(get_current_admin)):
    try: uid=uuid.UUID(post_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    p=db.get(Post, uid)
    if not p: raise HTTPException(status_code=404, detail="not_found")
    for k in ("title","slug","summary","content_md","tags"):
        if k in payload and payload[k] is not None:
            setattr(p, k, payload[k])
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="slug_conflict")
    db.refresh(p)
    return to_admin(p)

@router_admin.delete("/{post_id}")
def admin_delete(post_id: str, db: Session=Depends(get_db), admin=Depends(get_current_admin)):
    try: uid=uuid.UUID(post_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    p=db.get(Post, uid)
    if not p: raise HTTPException(status_code=404, detail="not_found")
    db.delete(p); db.commit()
    return {"ok": True}

@router_admin.post("/{post_id}/publish")
def publish(post_id: str, db: Session=Depends(get_db), admin=Depends(get_current_admin)):
    try: uid=uuid.UUID(post_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    p=db.get(Post, uid)
    if not p: raise HTTPException(status_code=404, detail="not_found")
    p.status="published"
    if not p.published_at:
        p.published_at=datetime.now(timezone.utc)
    db.add(p); db.commit(); db.refresh(p)
    return to_admin(p)

@router_admin.post("/{post_id}/unpublish")
def unpublish(post_id: str, db: Session=Depends(get_db), admin=Depends(get_current_admin)):
    try: uid=uuid.UUID(post_id)
    except ValueError: raise HTTPException(status_code=400, detail="invalid_id")
    p=db.get(Post, uid)
    if not p: raise HTTPException(status_code=404, detail="not_found")
    p.status="draft"
    db.add(p); db.commit(); db.refresh(p)
    return to_admin(p)
