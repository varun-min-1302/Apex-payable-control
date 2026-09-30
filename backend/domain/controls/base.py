from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID
from backend.database.models.ap import (
    Invoice,
    InvoiceRevision,
    InvoiceItem,
    ApprovalPolicy,
)
from backend.database.models.procurement import (
    Vendor,
    PurchaseOrder,
    PurchaseOrderItem,
    GoodsReceipt,
    GoodsReceiptItem,
)
from backend.application.dto.control_dto import (
    ControlEvaluation,
    ToleranceConfig,
)
from backend.database.enums import ControlCategory, ControlCode, ControlStatus, SeverityLevel

@dataclass(frozen=True)
class ControlContext:
    """
    Immutable domain context passed into every control evaluation.
    Loaded once per control run to eliminate N+1 query patterns.
    """
    tenant_id: UUID
    invoice: Invoice
    current_revision: InvoiceRevision
    invoice_items: list[InvoiceItem]
    vendor: Optional[Vendor]
    purchase_order: Optional[PurchaseOrder]
    po_items: list[PurchaseOrderItem]
    goods_receipts: list[GoodsReceipt]
    goods_receipt_items: list[GoodsReceiptItem]
    approval_policies: list[ApprovalPolicy]
    historical_invoices: list[Invoice] = field(default_factory=list)
    tolerance_config: ToleranceConfig = field(default_factory=ToleranceConfig)

class BaseControl(ABC):
    """Abstract base class for all deterministic AP controls."""
    control_code: str
    category: str
    rule_version: str = "v1.0"

    @abstractmethod
    def execute(self, context: ControlContext) -> ControlEvaluation:
        """
        Execute the control against the provided context.
        Must return an explainable ControlEvaluation (never just True/False).
        """
        pass
