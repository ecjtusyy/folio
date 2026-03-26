from __future__ import annotations
import secrets, time
from typing import Any
import jwt
from fastapi import HTTPException, Request, status
from .config import settings

SESSION_COOKIE_NAME="session"

def check_admin_credentials(username: str, password: str) -> bool:
    return secrets.compare_digest(username, settings.admin_username) and secrets.compare_digest(password, settings.admin_password)

def create_session_token() -> str:
    now=int(time.time())
    payload={"sub": settings.admin_username, "iat": now, "exp": now + settings.session_expire_hours*3600, "type":"session"}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def verify_session_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])

def require_admin(request: Request) -> str:
    tok=request.cookies.get(SESSION_COOKIE_NAME)
    if not tok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not_authenticated")
    try:
        payload=verify_session_token(tok)
        if payload.get("type")!="session":
            raise HTTPException(status_code=401, detail="invalid_session")
        return str(payload.get("sub"))
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="session_expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid_session")

def get_current_admin(request: Request) -> str:
    return require_admin(request)

def create_file_token(file_id: str, ttl_seconds: int) -> str:
    now=int(time.time())
    payload={"sub": file_id, "iat": now, "exp": now+ttl_seconds, "type":"file"}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def verify_file_token(token: str) -> str:
    payload=jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    if payload.get("type")!="file":
        raise HTTPException(status_code=403, detail="invalid_token")
    return str(payload.get("sub"))
