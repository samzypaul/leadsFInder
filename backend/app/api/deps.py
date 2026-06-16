"""Shared API dependencies (authentication)."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import decode_access_token
from app.database import get_db
from app.models import User

# auto_error=False so we can return a clean 401 (and respect AUTH_ENABLED).
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if not settings.auth_enabled:
        # Auth disabled: return (or lazily create) a system user.
        user = db.query(User).order_by(User.id).first()
        if user:
            return user
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "no users provisioned")

    if creds is None or not creds.credentials:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(creds.credentials)
    if not payload or "sub" not in payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")

    user = db.query(User).filter(User.email == payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user
