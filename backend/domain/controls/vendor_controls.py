from backend.domain.controls.base import BaseControl, ControlContext
from backend.application.dto.control_dto import ControlEvaluation
from backend.database.enums import ControlCategory, ControlCode, ControlStatus, SeverityLevel, VendorStatus

class VendorExistsControl(BaseControl):
    control_code = ControlCode.VENDOR_EXISTS.value
    category = ControlCategory.VENDOR.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        if context.vendor is not None and context.vendor.id == context.invoice.vendor_id:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.PASS,
                severity=SeverityLevel.INFO,
                message=f"Vendor exists and resolved: {context.vendor.display_name} ({context.vendor.vendor_code}).",
                expected_value={"vendor_id": str(context.invoice.vendor_id)},
                actual_value={"vendor_id": str(context.vendor.id), "vendor_code": context.vendor.vendor_code},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.FAIL,
            severity=SeverityLevel.CRITICAL,
            message=f"Referenced vendor ID '{context.invoice.vendor_id}' cannot be resolved in vendor master.",
            expected_value={"vendor_id": str(context.invoice.vendor_id)},
            actual_value={"resolved": False},
            rule_version=self.rule_version
        )

class VendorStatusControl(BaseControl):
    control_code = ControlCode.VENDOR_STATUS.value
    category = ControlCategory.VENDOR.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        if context.vendor is None:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.NOT_APPLICABLE,
                severity=SeverityLevel.INFO,
                message="Cannot evaluate vendor status because vendor record is missing.",
                rule_version=self.rule_version
            )

        vendor_status_str = str(context.vendor.status.value if hasattr(context.vendor.status, "value") else context.vendor.status)
        if vendor_status_str == VendorStatus.ACTIVE.value:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.PASS,
                severity=SeverityLevel.INFO,
                message=f"Vendor '{context.vendor.vendor_code}' is in ACTIVE status.",
                expected_value={"status": VendorStatus.ACTIVE.value},
                actual_value={"status": vendor_status_str},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.FAIL,
            severity=SeverityLevel.HIGH,
            message=f"Vendor '{context.vendor.vendor_code}' is {vendor_status_str}. Invoices cannot be processed for inactive or blocked vendors.",
            expected_value={"status": VendorStatus.ACTIVE.value},
            actual_value={"status": vendor_status_str},
            evidence={"vendor_id": str(context.vendor.id), "risk_status": str(context.vendor.risk_status)},
            rule_version=self.rule_version
        )

class VendorTaxIdMatchControl(BaseControl):
    control_code = ControlCode.VENDOR_TAX_ID_MATCH.value
    category = ControlCategory.VENDOR.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        if context.vendor is None:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.NOT_APPLICABLE,
                severity=SeverityLevel.INFO,
                message="Cannot evaluate tax ID match because vendor record is missing.",
                rule_version=self.rule_version
            )

        submitted_tax_id = (context.current_revision.vendor_tax_id_as_submitted or "").strip().upper()
        master_tax_id = (context.vendor.tax_identifier or "").strip().upper()

        if not submitted_tax_id:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.WARNING,
                severity=SeverityLevel.MEDIUM,
                message="Invoice did not include a vendor tax identifier (GSTIN/VAT).",
                expected_value={"tax_identifier": master_tax_id},
                actual_value={"submitted_tax_id": None},
                rule_version=self.rule_version
            )

        if submitted_tax_id == master_tax_id:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.PASS,
                severity=SeverityLevel.INFO,
                message=f"Invoice tax identifier matches vendor master: {master_tax_id}.",
                expected_value={"tax_identifier": master_tax_id},
                actual_value={"submitted_tax_id": submitted_tax_id},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.FAIL,
            severity=SeverityLevel.HIGH,
            message=f"Invoice tax identifier '{submitted_tax_id}' does not match vendor master record '{master_tax_id}'.",
            expected_value={"tax_identifier": master_tax_id},
            actual_value={"submitted_tax_id": submitted_tax_id},
            evidence={"vendor_code": context.vendor.vendor_code},
            rule_version=self.rule_version
        )

class BankDetailsMatchControl(BaseControl):
    control_code = ControlCode.BANK_DETAILS_MATCH.value
    category = ControlCategory.VENDOR.value

    def execute(self, context: ControlContext) -> ControlEvaluation:
        if context.vendor is None:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.NOT_APPLICABLE,
                severity=SeverityLevel.INFO,
                message="Cannot evaluate bank details match because vendor record is missing.",
                rule_version=self.rule_version
            )

        inv_hash = context.current_revision.bank_account_hash
        vendor_hash = context.vendor.bank_account_hash

        if not inv_hash or not vendor_hash:
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.WARNING,
                severity=SeverityLevel.MEDIUM,
                message="Bank account verification fingerprint is absent on invoice or vendor master.",
                expected_value={"has_vendor_bank_fingerprint": bool(vendor_hash)},
                actual_value={"has_invoice_bank_fingerprint": bool(inv_hash)},
                rule_version=self.rule_version
            )

        if inv_hash.strip().lower() == vendor_hash.strip().lower():
            return ControlEvaluation(
                control_code=self.control_code,
                category=self.category,
                status=ControlStatus.PASS,
                severity=SeverityLevel.INFO,
                message="Invoice bank account cryptographic fingerprint matches approved vendor banking details.",
                expected_value={"fingerprint_match": True},
                actual_value={"fingerprint_match": True},
                evidence={"bank_account_last4": context.vendor.bank_account_last4},
                rule_version=self.rule_version
            )

        return ControlEvaluation(
            control_code=self.control_code,
            category=self.category,
            status=ControlStatus.FAIL,
            severity=SeverityLevel.CRITICAL,
            message="HIGH RISK: Invoice bank account fingerprint does not match approved vendor banking records. Payment rerouting fraud suspected.",
            expected_value={"fingerprint_match": True},
            actual_value={"fingerprint_match": False},
            evidence={
                "vendor_bank_last4": context.vendor.bank_account_last4,
                "invoice_bank_last4": context.current_revision.bank_account_last4
            },
            rule_version=self.rule_version
        )
