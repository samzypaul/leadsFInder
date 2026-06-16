"""First-run provisioning (default admin user)."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import hash_password
from app.models import User

log = logging.getLogger("leadhunter.bootstrap")


def ensure_admin_user(db: Session) -> None:
    """Create the configured admin user if it doesn't already exist."""
    email = settings.admin_email.lower().strip()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return
    db.add(User(
        email=email,
        full_name="Administrator",
        password_hash=hash_password(settings.admin_password),
        is_active=True,
        is_admin=True,
    ))
    db.commit()
    log.info("Created default admin user: %s", email)
    if settings.admin_password == "changeme":
        log.warning("Default admin password in use — set ADMIN_PASSWORD before production!")
