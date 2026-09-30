from fastapi import APIRouter

from backend.api.v1.auth import router as auth_router
from backend.api.v1.invoices import router as invoices_router
from backend.api.v1.vendors import router as vendors_router
from backend.api.v1.purchase_orders import router as purchase_orders_router
from backend.api.v1.receipts import router as receipts_router
from backend.api.v1.controls import router as controls_router
from backend.api.v1.exceptions import router as exceptions_router
from backend.api.v1.approvals import router as approvals_router
from backend.api.v1.payables import router as payables_router
from backend.api.v1.dashboard import router as dashboard_router
from backend.api.v1.audit import router as audit_router
from backend.api.v1.scenarios import router as scenarios_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth_router)
api_v1_router.include_router(invoices_router)
api_v1_router.include_router(vendors_router)
api_v1_router.include_router(purchase_orders_router)
api_v1_router.include_router(receipts_router)
api_v1_router.include_router(controls_router)
api_v1_router.include_router(exceptions_router)
api_v1_router.include_router(approvals_router)
api_v1_router.include_router(payables_router)
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(scenarios_router)

__all__ = ["api_v1_router"]
