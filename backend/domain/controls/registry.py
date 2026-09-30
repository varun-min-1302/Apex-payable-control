from typing import Optional
from backend.domain.controls.base import BaseControl
from backend.domain.controls.vendor_controls import (
    VendorExistsControl,
    VendorStatusControl,
    VendorTaxIdMatchControl,
    BankDetailsMatchControl,
)
from backend.domain.controls.po_controls import (
    POExistsControl,
    POApprovedControl,
    POVendorMatchControl,
    POItemMatchControl,
)
from backend.domain.controls.receipt_controls import (
    ReceiptMatchControl,
    QuantityMatchControl,
)
from backend.domain.controls.financial_controls import (
    PriceMatchControl,
    TaxValidationControl,
    TotalValidationControl,
    PaymentTermsControl,
)
from backend.domain.controls.duplicate_controls import (
    DuplicateInvoiceControl,
    SemanticDuplicateControl,
)
from backend.domain.controls.risk_controls import (
    ThresholdProximityControl,
    UnusualAmountControl,
)

class ControlRegistry:
    """Registry maintaining active deterministic controls."""

    def __init__(self, controls: Optional[list[BaseControl]] = None):
        if controls is not None:
            self._controls = list(controls)
        else:
            self._controls = self.get_default_controls()

    @staticmethod
    def get_default_controls() -> list[BaseControl]:
        """Instantiate the standard 18 enterprise controls in deterministic evaluation sequence."""
        return [
            # A. Vendor Controls
            VendorExistsControl(),
            VendorStatusControl(),
            VendorTaxIdMatchControl(),
            BankDetailsMatchControl(),
            # B. Purchase Order Controls
            POExistsControl(),
            POApprovedControl(),
            POVendorMatchControl(),
            POItemMatchControl(),
            # C. Receipt Controls
            ReceiptMatchControl(),
            QuantityMatchControl(),
            # D. Financial Controls
            PriceMatchControl(),
            TaxValidationControl(),
            TotalValidationControl(),
            PaymentTermsControl(),
            # E. Duplicate Controls
            DuplicateInvoiceControl(),
            SemanticDuplicateControl(),
            # F. Risk Controls
            ThresholdProximityControl(),
            UnusualAmountControl(),
        ]

    @property
    def controls(self) -> list[BaseControl]:
        return list(self._controls)

    def get_control(self, control_code: str) -> Optional[BaseControl]:
        for c in self._controls:
            if c.control_code == control_code:
                return c
        return None

# Singleton default registry instance
default_registry = ControlRegistry()
