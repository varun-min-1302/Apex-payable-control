import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import Any
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Date,
    Integer,
    Numeric,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from backend.database.models.base import Base
from backend.database.models.identity import User
from backend.database.models.procurement import Vendor, PurchaseOrder

class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("tenant_id", "vendor_id", "invoice_number", name="uq_invoices_tenant_vendor_invoice_num"),
        Index("ix_invoices_tenant_id", "tenant_id"),
        Index("ix_invoices_vendor_id", "vendor_id"),
        Index("ix_invoices_po_id", "purchase_order_id"),
        Index("ix_invoices_invoice_number", "invoice_number"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_due_date", "due_date"),
        Index("ix_invoices_document_hash", "document_hash"),
        Index("ix_invoices_created_at", "created_at"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("procurement.vendors.id", ondelete="RESTRICT"), nullable=False
    )
    purchase_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("procurement.purchase_orders.id", ondelete="SET NULL"), nullable=True
    )
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="RECEIVED")
    current_revision_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="UPLOAD")
    source_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    document_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(50), nullable=False, default="NOT_STARTED")
    extraction_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor", foreign_keys="Invoice.vendor_id")
    purchase_order: Mapped["PurchaseOrder | None"] = relationship("PurchaseOrder", foreign_keys="Invoice.purchase_order_id")
    revisions: Mapped[list["InvoiceRevision"]] = relationship("InvoiceRevision", back_populates="invoice", cascade="all, delete-orphan", foreign_keys="InvoiceRevision.invoice_id")
    control_runs: Mapped[list["ControlRun"]] = relationship("ControlRun", back_populates="invoice", cascade="all, delete-orphan")
    control_results: Mapped[list["ControlResult"]] = relationship("ControlResult", back_populates="invoice", cascade="all, delete-orphan")
    risk_signals: Mapped[list["RiskSignal"]] = relationship("RiskSignal", back_populates="invoice", cascade="all, delete-orphan")
    exceptions: Mapped[list["Exception"]] = relationship("Exception", back_populates="invoice", cascade="all, delete-orphan")
    approvals: Mapped[list["Approval"]] = relationship("Approval", back_populates="invoice", cascade="all, delete-orphan")
    payable: Mapped["PayableLedger | None"] = relationship("PayableLedger", back_populates="invoice", uselist=False)
    documents: Mapped[list["InvoiceDocument"]] = relationship("InvoiceDocument", back_populates="invoice")

class InvoiceRevision(Base):
    __tablename__ = "invoice_revisions"
    __table_args__ = (
        UniqueConstraint("invoice_id", "revision_number", name="uq_invoice_revisions_invoice_rev_num"),
        CheckConstraint("subtotal >= 0", name="ck_invoice_rev_subtotal_positive"),
        CheckConstraint("tax_total >= 0", name="ck_invoice_rev_tax_total_positive"),
        CheckConstraint("discount_total >= 0", name="ck_invoice_rev_discount_positive"),
        CheckConstraint("grand_total >= 0", name="ck_invoice_rev_grand_total_positive"),
        Index("ix_invoice_revisions_tenant_id", "tenant_id"),
        Index("ix_invoice_revisions_invoice_id", "invoice_id"),
        Index("ix_invoice_revisions_invoice_number", "invoice_number"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    vendor_name_as_submitted: Mapped[str | None] = mapped_column(String(255), nullable=True)
    vendor_tax_id_as_submitted: Mapped[str | None] = mapped_column(String(50), nullable=True)
    bank_account_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    bank_account_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    extraction_method: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extraction_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    raw_extracted_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="revisions", foreign_keys=[invoice_id])
    items: Mapped[list["InvoiceItem"]] = relationship("InvoiceItem", back_populates="revision", cascade="all, delete-orphan")
    control_runs: Mapped[list["ControlRun"]] = relationship("ControlRun", back_populates="revision")

class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (
        UniqueConstraint("invoice_revision_id", "line_number", name="uq_invoice_items_rev_line_number"),
        CheckConstraint("quantity > 0", name="ck_invoice_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_invoice_items_unit_price_positive"),
        CheckConstraint("tax_rate >= 0", name="ck_invoice_items_tax_rate_positive"),
        CheckConstraint("discount_amount >= 0", name="ck_invoice_items_discount_positive"),
        CheckConstraint("line_total >= 0", name="ck_invoice_items_line_total_positive"),
        Index("ix_invoice_items_tenant_id", "tenant_id"),
        Index("ix_invoice_items_revision_id", "invoice_revision_id"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    invoice_revision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoice_revisions.id", ondelete="CASCADE"), nullable=False
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    product_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_of_measure: Mapped[str] = mapped_column(String(20), nullable=False, default="EA")
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=Decimal("0.0000"))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    revision: Mapped["InvoiceRevision"] = relationship("InvoiceRevision", back_populates="items")

class ControlRun(Base):
    __tablename__ = "control_runs"
    __table_args__ = (
        UniqueConstraint("invoice_revision_id", "run_number", name="uq_control_runs_rev_run_number"),
        Index("ix_control_runs_tenant_id", "tenant_id"),
        Index("ix_control_runs_invoice_id", "invoice_id"),
        Index("ix_control_runs_revision_id", "invoice_revision_id"),
        Index("ix_control_runs_status", "status"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False
    )
    invoice_revision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoice_revisions.id", ondelete="CASCADE"), nullable=False
    )
    run_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="RUNNING")
    ruleset_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    triggered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="control_runs")
    revision: Mapped["InvoiceRevision"] = relationship("InvoiceRevision", back_populates="control_runs")
    results: Mapped[list["ControlResult"]] = relationship("ControlResult", back_populates="control_run", cascade="all, delete-orphan")

class ControlResult(Base):
    __tablename__ = "control_results"
    __table_args__ = (
        UniqueConstraint("control_run_id", "control_code", name="uq_control_results_run_code"),
        Index("ix_control_results_tenant_id", "tenant_id"),
        Index("ix_control_results_run_id", "control_run_id"),
        Index("ix_control_results_invoice_id", "invoice_id"),
        Index("ix_control_results_code", "control_code"),
        Index("ix_control_results_status", "status"),
        Index("ix_control_results_severity", "severity"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    control_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.control_runs.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False
    )
    control_code: Mapped[str] = mapped_column(String(50), nullable=False)
    control_category: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    expected_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    actual_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    variance_value: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    variance_percentage: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    rule_version: Mapped[str] = mapped_column(String(50), nullable=False, default="v1.0")
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    control_run: Mapped["ControlRun"] = relationship("ControlRun", back_populates="results")
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="control_results")
    risk_signals: Mapped[list["RiskSignal"]] = relationship("RiskSignal", back_populates="control_result")
    exceptions: Mapped[list["Exception"]] = relationship("Exception", back_populates="control_result")

class RiskSignal(Base):
    __tablename__ = "risk_signals"
    __table_args__ = (
        Index("ix_risk_signals_tenant_id", "tenant_id"),
        Index("ix_risk_signals_invoice_id", "invoice_id"),
        Index("ix_risk_signals_signal_code", "signal_code"),
        Index("ix_risk_signals_category", "category"),
        Index("ix_risk_signals_severity", "severity"),
        Index("ix_risk_signals_status", "status"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False
    )
    control_result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.control_results.id", ondelete="SET NULL"), nullable=True
    )
    signal_code: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="risk_signals")
    control_result: Mapped["ControlResult | None"] = relationship("ControlResult", back_populates="risk_signals")

class Exception(Base):
    __tablename__ = "exceptions"
    __table_args__ = (
        Index("ix_exceptions_tenant_id", "tenant_id"),
        Index("ix_exceptions_invoice_id", "invoice_id"),
        Index("ix_exceptions_code", "exception_code"),
        Index("ix_exceptions_severity", "severity"),
        Index("ix_exceptions_status", "status"),
        Index("ix_exceptions_assigned_to", "assigned_to"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False
    )
    control_result_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.control_results.id", ondelete="SET NULL"), nullable=True
    )
    exception_code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="OPEN")
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="exceptions")
    control_result: Mapped["ControlResult | None"] = relationship("ControlResult", back_populates="exceptions")
    assignee: Mapped["User | None"] = relationship("User", foreign_keys="Exception.assigned_to")

class ApprovalPolicy(Base):
    __tablename__ = "approval_policies"
    __table_args__ = (
        CheckConstraint("min_amount >= 0", name="ck_approval_policies_min_amount_positive"),
        Index("ix_approval_policies_tenant_id", "tenant_id"),
        Index("ix_approval_policies_active", "active"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    min_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True)
    required_role: Mapped[str] = mapped_column(String(50), nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    requires_all_controls_pass: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    approvals: Mapped[list["Approval"]] = relationship("Approval", back_populates="policy")

class Approval(Base):
    __tablename__ = "approvals"
    __table_args__ = (
        UniqueConstraint("invoice_id", "sequence_order", name="uq_approvals_invoice_seq"),
        Index("ix_approvals_tenant_id", "tenant_id"),
        Index("ix_approvals_invoice_id", "invoice_id"),
        Index("ix_approvals_approver_id", "approver_user_id"),
        Index("ix_approvals_status", "status"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False
    )
    approval_policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.approval_policies.id", ondelete="RESTRICT"), nullable=False
    )
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    approver_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    decision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="approvals")
    policy: Mapped["ApprovalPolicy"] = relationship("ApprovalPolicy", back_populates="approvals")

class PayableLedger(Base):
    __tablename__ = "payable_ledger"
    __table_args__ = (
        UniqueConstraint("tenant_id", "invoice_id", name="uq_payable_ledger_tenant_invoice"),
        UniqueConstraint("tenant_id", "payable_number", name="uq_payable_ledger_tenant_payable_num"),
        CheckConstraint("approved_amount > 0", name="ck_payable_ledger_approved_amount_positive"),
        Index("ix_payable_ledger_tenant_id", "tenant_id"),
        Index("ix_payable_ledger_vendor_id", "vendor_id"),
        Index("ix_payable_ledger_status", "status"),
        Index("ix_payable_ledger_due_date", "due_date"),
        Index("ix_payable_ledger_payable_number", "payable_number"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoices.id", ondelete="RESTRICT"), nullable=False
    )
    invoice_revision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoice_revisions.id", ondelete="RESTRICT"), nullable=False
    )
    vendor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("procurement.vendors.id", ondelete="RESTRICT"), nullable=False
    )
    payable_number: Mapped[str] = mapped_column(String(50), nullable=False)
    approved_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="OPEN")
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payable")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="payable", cascade="all, delete-orphan")

class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "payment_reference", name="uq_payments_tenant_payment_ref"),
        CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        Index("ix_payments_tenant_id", "tenant_id"),
        Index("ix_payments_payable_id", "payable_id"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_payment_date", "payment_date"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    payable_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.payable_ledger.id", ondelete="RESTRICT"), nullable=False
    )
    payment_reference: Mapped[str] = mapped_column(String(100), nullable=False)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="SCHEDULED")
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False, default="NEFT")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    payable: Mapped["PayableLedger"] = relationship("PayableLedger", back_populates="payments")

class InvoiceEmbedding(Base):
    __tablename__ = "invoice_embeddings"
    __table_args__ = (
        Index("ix_invoice_embeddings_tenant_id", "tenant_id"),
        Index("ix_invoice_embeddings_invoice_id", "invoice_id"),
        Index("ix_invoice_embeddings_revision_id", "invoice_revision_id"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False
    )
    invoice_revision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoice_revisions.id", ondelete="CASCADE"), nullable=False
    )
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), nullable=True)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    source_text_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

class InvoiceDocument(Base):
    __tablename__ = "invoice_documents"
    __table_args__ = (
        Index("ix_invoice_documents_tenant_id", "tenant_id"),
        Index("ix_invoice_documents_invoice_id", "invoice_id"),
        Index("ix_invoice_documents_sha256_hash", "sha256_hash"),
        Index("ix_invoice_documents_tenant_hash", "tenant_id", "sha256_hash"),
        Index("ix_invoice_documents_created_at", "created_at"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoices.id", ondelete="SET NULL"), nullable=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    sanitized_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="UPLOAD")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="READY_FOR_EXTRACTION")
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    invoice: Mapped["Invoice | None"] = relationship("Invoice", foreign_keys="InvoiceDocument.invoice_id", back_populates="documents")
    uploader: Mapped["User | None"] = relationship("User", foreign_keys="InvoiceDocument.uploaded_by")
    drafts: Mapped[list["InvoiceDraft"]] = relationship("InvoiceDraft", back_populates="document", cascade="all, delete-orphan")

class InvoiceDraft(Base):
    __tablename__ = "invoice_drafts"
    __table_args__ = (
        Index("ix_invoice_drafts_tenant_id", "tenant_id"),
        Index("ix_invoice_drafts_document_id", "document_id"),
        Index("ix_invoice_drafts_status", "status"),
        Index("ix_invoice_drafts_confirmed_invoice_id", "confirmed_invoice_id"),
        Index("ix_invoice_drafts_created_at", "created_at"),
        {"schema": "ap"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoice_documents.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="EXTRACTED")
    extracted_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    field_confidences: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    overall_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    warnings: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)
    vendor_match: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    confirmed_invoice_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ap.invoices.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    document: Mapped["InvoiceDocument"] = relationship("InvoiceDocument", foreign_keys="InvoiceDraft.document_id", back_populates="drafts")
    confirmed_invoice: Mapped["Invoice | None"] = relationship("Invoice", foreign_keys="InvoiceDraft.confirmed_invoice_id")
    reviewer: Mapped["User | None"] = relationship("User", foreign_keys="InvoiceDraft.reviewed_by")
