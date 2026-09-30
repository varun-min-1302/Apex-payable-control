from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.database.models.procurement import Vendor

class VendorRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, tenant_id: UUID, vendor_id: UUID) -> Optional[Vendor]:
        """Fetch vendor by tenant and ID."""
        stmt = (
            select(Vendor)
            .where(Vendor.tenant_id == tenant_id, Vendor.id == vendor_id)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_code(self, tenant_id: UUID, vendor_code: str) -> Optional[Vendor]:
        """Fetch vendor by tenant and vendor code."""
        stmt = (
            select(Vendor)
            .where(Vendor.tenant_id == tenant_id, Vendor.vendor_code == vendor_code.strip())
        )
        return self.session.execute(stmt).scalar_one_or_none()
