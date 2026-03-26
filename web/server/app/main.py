from __future__ import annotations
import os
import time
import uuid as uuidlib
import logging
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from .config import settings
from .storage import ensure_bucket
from .routers.health import router as health_router
from .routers.auth import router as auth_router
from .routers.notes import router as notes_router
from .routers.posts import router_public, router_admin
from .routers.files import router as files_router
from .routers.imports import router as imports_router, router_public as imports_public, router_library as library_router
from .routers.onlyoffice import router as onlyoffice_router

app = FastAPI(title="Monorepo API")

logger = logging.getLogger("app")

def setup_logging():
    os.makedirs(settings.app_log_dir, exist_ok=True)
    path = os.path.join(settings.app_log_dir, "server.log")
    handler = RotatingFileHandler(path, maxBytes=10_000_000, backupCount=3, encoding="utf-8")
    fmt = logging.Formatter("%(asctime)s %(levelname)s req=%(request_id)s %(message)s")
    handler.setFormatter(fmt)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

@app.on_event("startup")
def startup():
    os.makedirs(settings.app_tmp_dir, exist_ok=True)
    setup_logging()
    try:
        ensure_bucket()
    except Exception as e:
        logger.warning("minio bucket ensure failed: %s", e, extra={"request_id":"startup"})

@app.middleware("http")
async def request_mw(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or uuidlib.uuid4().hex
    start = time.time()
    try:
        resp: Response = await call_next(request)
        dur_ms = int((time.time()-start)*1000)
        logger.info("%s %s -> %s %sms", request.method, request.url.path, resp.status_code, dur_ms, extra={"request_id":rid})
        resp.headers["X-Request-ID"] = rid
        return resp
    except Exception as e:
        dur_ms = int((time.time()-start)*1000)
        logger.exception("unhandled error %s %s after %sms: %s", request.method, request.url.path, dur_ms, e, extra={"request_id":rid})
        return JSONResponse(status_code=500, content={"detail":"internal_error","request_id":rid})

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(notes_router)
app.include_router(router_public)
app.include_router(router_admin)
app.include_router(files_router)
app.include_router(imports_router)
app.include_router(imports_public)
app.include_router(library_router)
app.include_router(onlyoffice_router)
