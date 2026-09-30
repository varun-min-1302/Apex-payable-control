from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from backend.api.deps import get_db, get_current_user
from backend.database.models.identity import User, UserRole, Role, Tenant
from backend.core.security import create_access_token
from backend.api.schemas.auth_schemas import LoginRequest, TokenResponse, UserOut, DemoUserOut

router = APIRouter(prefix="/auth", tags=["Authentication & Identity"])

DEMO_ACCOUNTS = [
    {
        "email": "rajesh.sharma@apexfin.in",
        "full_name": "Rajesh Sharma",
        "roles": ["ADMIN"],
        "description": "System Administrator with unrestricted access across all modules."
    },
    {
        "email": "priya.nair@apexfin.in",
        "full_name": "Priya Nair",
        "roles": ["AP_CLERK"],
        "description": "AP Clerk responsible for invoice intake, correction, and initial reviews."
    },
    {
        "email": "vikram.malhotra@apexfin.in",
        "full_name": "Vikram Malhotra",
        "roles": ["PROCUREMENT_MANAGER"],
        "description": "Procurement Manager reviewing purchase order and pricing discrepancies."
    },
    {
        "email": "sneha.kulkarni@apexfin.in",
        "full_name": "Sneha Kulkarni",
        "roles": ["RECEIVING_USER"],
        "description": "Receiving Specialist handling warehouse goods receipts and quantity variances."
    },
    {
        "email": "ananya.rao@apexfin.in",
        "full_name": "Ananya Rao",
        "roles": ["FINANCE_MANAGER"],
        "description": "Finance Manager authorized to approve Tier 2 invoices (up to ₹500,000)."
    },
    {
        "email": "rohan.verma@apexfin.in",
        "full_name": "Rohan Verma",
        "roles": ["FINANCE_HEAD"],
        "description": "Head of Finance authorized for executive approvals (up to ₹2,500,000)."
    },
    {
        "email": "sunita.mehta@apexfin.in",
        "full_name": "Sunita Mehta",
        "roles": ["AUDITOR"],
        "description": "Compliance Auditor with read-only view of audit logs and control runs."
    },
]

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user by email address and return a signed JWT access token.
    For hackathon demo convenience, valid seeded user emails log in directly.
    """
    user = (
        db.query(User)
        .options(joinedload(User.user_roles).joinedload(UserRole.role))
        .filter(User.email == payload.email.strip().lower(), User.status == "ACTIVE")
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or inactive user account."
        )

    roles = [ur.role.code for ur in user.user_roles if ur.role and ur.role.code]
    token = create_access_token(
        user_id=user.id,
        tenant_id=user.tenant_id,
        email=user.email,
        roles=roles
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserOut(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            full_name=user.full_name,
            status=user.status,
            roles=roles
        )
    )

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    """Retrieve the profile and role assignments of the currently authenticated actor."""
    return UserOut(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        email=current_user.email,
        full_name=current_user.full_name,
        status=current_user.status,
        roles=getattr(current_user, "role_codes", [])
    )

@router.get("/demo-users", response_model=list[DemoUserOut])
def list_demo_users():
    """List preset enterprise persona accounts for rapid demo persona switching."""
    return [DemoUserOut(**account) for account in DEMO_ACCOUNTS]
