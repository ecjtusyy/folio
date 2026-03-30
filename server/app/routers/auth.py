from __future__ import annotations
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse
from ..auth import SESSION_COOKIE_NAME, check_admin_credentials, create_session_token, verify_session_token
from ..config import settings

router=APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login")
def login(payload: dict, response: Response):
    username=payload.get("username","")
    password=payload.get("password","")
    if not check_admin_credentials(username, password):
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail":"invalid_credentials"})
    token=create_session_token()
    response.set_cookie(
        key=SESSION_COOKIE_NAME, value=token, httponly=True, samesite="lax", secure=False, path="/",
        max_age=60*60*settings.session_expire_hours
    )
    return {"ok": True}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return {"ok": True}

@router.get("/me")
def me(request: Request):
    tok=request.cookies.get(SESSION_COOKIE_NAME)
    if not tok:
        return {"authenticated": False}
    try:
        verify_session_token(tok)
    except Exception:
        return {"authenticated": False}
    return {"authenticated": True, "username": settings.admin_username}
