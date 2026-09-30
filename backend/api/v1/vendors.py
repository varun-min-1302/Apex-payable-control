from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from backend.api.deps import get_db, get_current_user
from backend.database.models.identity import User
from backend.database.models.procurement import Vendor
from backend.database.models.ap import Invoice
from backend.api.schemas.vendor_schemas import VendorOut, VendorDetailOut

router = APIRouter(prefix="/vendors", tags=["Vendors"])

@router.get("", response_model=list[VendorOut])
def list_vendors(
    status_filter: Optional[str] = Query(None, alias="status"),
    risk_status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List vendors in the active tenant with optional status and text search filtering."""
    stmt = (
        select(Vendor)
        .where(Vendor.tenant_id == current_user.tenant_id)
        .order_by(Vendor.vendor_code)
    )

    if status_filter:
        stmt = stmt.where(Vendor.status == status_filter.upper())
    if risk_status:
        stmt = stmt.where(Vendor.risk_status == risk_status.upper())
    if search:
        search_term = f"%{search.strip().lower()}%"
        stmt = stmt.where(
            func.lower(Vendor.legal_name).like(search_term) |
            func.lower(Vendor.vendor_code).like(search_term)
        )

    stmt = stmt.offset(offset).limit(limit)
    vendors = db.execute(stmt).scalars().all()
    return [VendorOut.model_validate(v) for v in vendors]

@router.get("/{vendor_id}", response_model=VendorDetailOut)
def get_vendor_detail(
    vendor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve comprehensive vendor master record with aggregate invoice volume counts."""
    vendor = db.query(Vendor).filter(
        Vendor.tenant_id == current_user.tenant_id,
        Vendor.id == vendor_id
    ).first()

    if not vendor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found.")

    total_invoices = db.query(Invoice).filter(
        Invoice.tenant_id == current_user.tenant_id,
        Invoice.vendor_id == vendor_id
    ).count()

    open_invoices = db.query(Invoice).filter(
        Invoice.tenant_id == current_user.tenant_id,
        Invoice.vendor_id == vendor_id,
        Invoice.status.in_(["RECEIVED", "VALIDATING", "EXCEPTION", "AWAITING_APPROVAL"])
    ).count()

    return VendorDetailOut(
        **VendorOut.model_validate(vendor).model_dump(),
        email=vendor.email,
        phone=vendor.phone,
        address=vendor.address,
        total_invoices_count=total_invoices,
        open_invoices_count=open_invoices
    )
