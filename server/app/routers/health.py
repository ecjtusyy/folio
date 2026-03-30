from __future__ import annotations
import shutil
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..config import settings
from ..db import get_db
from ..storage import get_s3_client

router=APIRouter(prefix="/api", tags=["health"])

@router.get("/health")
def health(db: Session = Depends(get_db)):
    db_ok=minio_ok=only_ok=False
    only_text=None
    try:
        db.execute(text("SELECT 1"))
        db_ok=True
    except Exception:
        pass
    try:
        get_s3_client().list_buckets()
        minio_ok=True
    except Exception:
        pass
    try:
        r=httpx.get(f"{settings.onlyoffice_internal_url}/healthcheck", timeout=2.0)
        only_text=(r.text or "").strip()
        only_ok = (r.status_code==200 and only_text.lower()=="true")
    except Exception:
        pass
    tex_ok = shutil.which("latexmk") is not None
    status_="ok" if (db_ok and minio_ok and only_ok and tex_ok) else "degraded"
    return {
        "status": status_,
        "db": {"ok": db_ok},
        "minio": {"ok": minio_ok},
        "onlyoffice": {"ok": only_ok, "healthcheck": only_text},
        "tex": {"latexmk": tex_ok}
    }
