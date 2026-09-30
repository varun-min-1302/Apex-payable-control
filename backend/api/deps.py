from typing import Generator, Optional, Callable, Any
from uuid import UUID
from fastapi import Depends, HTTPException, status, Header, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from backend.database.session import SessionLocal
from backend.database.models.identity import User, UserRole, Role, Tenant
from backend.core.security import decode_access_token
from backend.application.storage.base import DocumentStorage

security_scheme = HTTPBearer(auto_error=False)

def get_db() -> Generator[Session, None, None]:
    """Dependency that creates and closes a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(
    db: Session = Depends(get_db),
    auth_creds: Optional[HTTPAuthorizationCredentials] = Security(security_scheme),
    x_demo_user_email: Optional[str] = Header(None, alias="X-Demo-User-Email")
) -> User:
    """
    Authenticate the current user via JWT bearer token or X-Demo-User-Email header.
    Loads the user with their active role codes.
    """
    user: Optional[User] = None

    # 1. First check JWT Bearer token
    if auth_creds and auth_creds.credentials:
        payload = decode_access_token(auth_creds.credentials)
        if payload and "sub" in payload:
            user_id = UUID(payload["sub"])
            user = (
                db.query(User)
                .options(joinedload(User.user_roles).joinedload(UserRole.role))
                .filter(User.id == user_id, User.status == "ACTIVE")
                .first()
            )

    # 2. Fallback to X-Demo-User-Email for frontend demo role switching
    if not user and x_demo_user_email:
        user = (
            db.query(User)
            .options(joinedload(User.user_roles).joinedload(UserRole.role))
            .filter(User.email == x_demo_user_email.strip().lower(), User.status == "ACTIVE")
            .first()
        )

    # 3. Default fallback to Admin for local development/interactive Swagger testing ONLY if no header was provided
    if not user and not x_demo_user_email and not (auth_creds and auth_creds.credentials):
        # Check if default admin exists
        user = (
            db.query(User)
            .options(joinedload(User.user_roles).joinedload(UserRole.role))
            .filter(User.email == "rajesh.sharma@apexfin.in", User.status == "ACTIVE")
            .first()
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or user is inactive.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Attach computed role codes to user object for easy inspection
    user.role_codes = [ur.role.code for ur in user.user_roles if ur.role and ur.role.code]
    return user

def require_roles(*allowed_roles: Any) -> Callable[[User], User]:
    """
    Dependency factory ensuring the current user possesses at least one of the specified roles.
    ADMIN is always granted access.
    Accepts both variable arguments ('ROLE_A', 'ROLE_B') and collections (['ROLE_A', 'ROLE_B']).
    """
    flat_roles: list[str] = []
    for r in allowed_roles:
        if isinstance(r, (list, tuple, set)):
            flat_roles.extend(str(item) for item in r)
        elif r is not None:
            flat_roles.append(str(r))

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_roles = getattr(current_user, "role_codes", [])
        if "ADMIN" in user_roles:
            return current_user

        has_role = any(r in user_roles for r in flat_roles)
        if not has_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of the following roles: {', '.join(flat_roles)}. Current roles: {', '.join(user_roles)}."
            )
        return current_user

    return role_checker

_storage_instance: Optional[DocumentStorage] = None

def get_storage() -> DocumentStorage:
    """Dependency supplying the configured DocumentStorage provider."""
    global _storage_instance
    if _storage_instance is None:
        from backend.application.storage.local import LocalStorageProvider
        _storage_instance = LocalStorageProvider()
    return _storage_instance
