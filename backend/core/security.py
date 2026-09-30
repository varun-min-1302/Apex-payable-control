import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Any
from uuid import UUID
import jwt

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ap-control-dev-super-secret-key-2026-finathon")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def create_access_token(
    user_id: UUID,
    tenant_id: UUID,
    email: str,
    roles: list[str],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a signed JWT access token containing identity claims."""
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tenant_id": str(tenant_id),
        "email": email,
        "roles": roles,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
