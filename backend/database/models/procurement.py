import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    String,
    Text,
    DateTime,
    Date,
    Integer,
    Numeric,
    ForeignKey,
    UniqueConstraint,
    CheckConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database.models.base import Base

class Vendor(Base):
    __tablename__ = "vendors"
    __table_args__ = (
        UniqueConstraint("tenant_id", "vendor_code", name="uq_vendors_tenant_vendor_code"),
        Index("ix_vendors_tenant_id", "tenant_id"),
        Index("ix_vendors_status", "status"),
        Index("ix_vendors_risk_status", "risk_status"),
        Index("ix_vendors_tax_identifier", "tax_identifier"),
        Index("ix_vendors_legal_name", "legal_name"),
        {"schema": "procurement"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    vendor_code: Mapped[str] = mapped_column(String(50), nullable=False)
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tax_identifier: Mapped[str | None] = mapped_column(String(50), nullable=True) # GSTIN
    registration_number: Mapped[str | None] = mapped_column(String(100), nullable=True) # CIN/PAN
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="India")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    payment_terms_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")
    risk_status: Mapped[str] = mapped_column(String(50), nullable=False, default="NORMAL")
    bank_account_last4: Mapped[str | None] = mapped_column(String(4), nullable=True)
    bank_account_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ifsc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    purchase_orders: Mapped[list["PurchaseOrder"]] = relationship("PurchaseOrder", back_populates="vendor")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        UniqueConstraint("tenant_id", "po_number", name="uq_purchase_orders_tenant_po_number"),
        CheckConstraint("subtotal >= 0", name="ck_purchase_orders_subtotal_positive"),
        CheckConstraint("tax_total >= 0", name="ck_purchase_orders_tax_total_positive"),
        CheckConstraint("discount_total >= 0", name="ck_purchase_orders_discount_total_positive"),
        CheckConstraint("grand_total >= 0", name="ck_purchase_orders_grand_total_positive"),
        Index("ix_purchase_orders_tenant_id", "tenant_id"),
        Index("ix_purchase_orders_vendor_id", "vendor_id"),
        Index("ix_purchase_orders_po_number", "po_number"),
        Index("ix_purchase_orders_status", "status"),
        Index("ix_purchase_orders_po_date", "po_date"),
        {"schema": "procurement"},
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
    po_number: Mapped[str] = mapped_column(String(50), nullable=False)
    po_date: Mapped[date] = mapped_column(Date, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")
    approval_status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")
    payment_terms_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    discount_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    grand_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=Decimal("0.00"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship("Vendor", back_populates="purchase_orders")
    items: Mapped[list["PurchaseOrderItem"]] = relationship("PurchaseOrderItem", back_populates="purchase_order", cascade="all, delete-orphan")
    goods_receipts: Mapped[list["GoodsReceipt"]] = relationship("GoodsReceipt", back_populates="purchase_order")

class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    __table_args__ = (
        UniqueConstraint("purchase_order_id", "line_number", name="uq_po_items_po_line_number"),
        CheckConstraint("quantity > 0", name="ck_po_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_po_items_unit_price_positive"),
        CheckConstraint("tax_rate >= 0", name="ck_po_items_tax_rate_positive"),
        CheckConstraint("discount_amount >= 0", name="ck_po_items_discount_positive"),
        CheckConstraint("line_total >= 0", name="ck_po_items_line_total_positive"),
        Index("ix_po_items_tenant_id", "tenant_id"),
        Index("ix_po_items_purchase_order_id", "purchase_order_id"),
        {"schema": "procurement"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("procurement.purchase_orders.id", ondelete="CASCADE"), nullable=False
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
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="items")
    receipt_items: Mapped[list["GoodsReceiptItem"]] = relationship("GoodsReceiptItem", back_populates="purchase_order_item")

class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"
    __table_args__ = (
        UniqueConstraint("tenant_id", "receipt_number", name="uq_goods_receipts_tenant_receipt_number"),
        Index("ix_goods_receipts_tenant_id", "tenant_id"),
        Index("ix_goods_receipts_purchase_order_id", "purchase_order_id"),
        Index("ix_goods_receipts_receipt_number", "receipt_number"),
        Index("ix_goods_receipts_status", "status"),
        Index("ix_goods_receipts_received_date", "received_date"),
        {"schema": "procurement"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    purchase_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("procurement.purchase_orders.id", ondelete="RESTRICT"), nullable=False
    )
    receipt_number: Mapped[str] = mapped_column(String(50), nullable=False)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACCEPTED")
    received_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship("PurchaseOrder", back_populates="goods_receipts")
    items: Mapped[list["GoodsReceiptItem"]] = relationship("GoodsReceiptItem", back_populates="goods_receipt", cascade="all, delete-orphan")

class GoodsReceiptItem(Base):
    __tablename__ = "goods_receipt_items"
    __table_args__ = (
        CheckConstraint("received_quantity >= 0", name="ck_gr_items_received_qty_positive"),
        CheckConstraint("accepted_quantity >= 0", name="ck_gr_items_accepted_qty_positive"),
        CheckConstraint("rejected_quantity >= 0", name="ck_gr_items_rejected_qty_positive"),
        CheckConstraint(
            "accepted_quantity + rejected_quantity <= received_quantity",
            name="ck_gr_items_accepted_plus_rejected_lte_received",
        ),
        Index("ix_gr_items_tenant_id", "tenant_id"),
        Index("ix_gr_items_goods_receipt_id", "goods_receipt_id"),
        Index("ix_gr_items_po_item_id", "purchase_order_item_id"),
        {"schema": "procurement"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False
    )
    goods_receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("procurement.goods_receipts.id", ondelete="CASCADE"), nullable=False
    )
    purchase_order_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("procurement.purchase_order_items.id", ondelete="RESTRICT"), nullable=False
    )
    received_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    accepted_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    rejected_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, default=Decimal("0.0000"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    goods_receipt: Mapped["GoodsReceipt"] = relationship("GoodsReceipt", back_populates="items")
    purchase_order_item: Mapped["PurchaseOrderItem"] = relationship("PurchaseOrderItem", back_populates="receipt_items")
