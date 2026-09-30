"""Initial multi-schema AP control system database

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-30 14:35:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "btree_gist"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')

    # 2. Schemas
    op.execute("CREATE SCHEMA IF NOT EXISTS identity")
    op.execute("CREATE SCHEMA IF NOT EXISTS procurement")
    op.execute("CREATE SCHEMA IF NOT EXISTS ap")
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")

    # 3. identity.tenants
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="identity",
    )
    op.create_index("ix_tenants_status", "tenants", ["status"], schema="identity")

    # 4. identity.users
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        schema="identity",
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"], schema="identity")
    op.create_index("ix_users_email", "users", ["email"], schema="identity")
    op.create_index("ix_users_status", "users", ["status"], schema="identity")

    # 5. identity.roles
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="identity",
    )

    # 6. identity.user_roles
    op.create_table(
        "user_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_roles_user_role"),
        schema="identity",
    )
    op.create_index("ix_user_roles_tenant_id", "user_roles", ["tenant_id"], schema="identity")

    # 7. procurement.vendors
    op.create_table(
        "vendors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_code", sa.String(50), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("tax_identifier", sa.String(50), nullable=True),
        sa.Column("registration_number", sa.String(100), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="India"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("risk_status", sa.String(50), nullable=False, server_default="NORMAL"),
        sa.Column("bank_account_last4", sa.String(4), nullable=True),
        sa.Column("bank_account_hash", sa.String(64), nullable=True),
        sa.Column("bank_name", sa.String(100), nullable=True),
        sa.Column("ifsc", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "vendor_code", name="uq_vendors_tenant_vendor_code"),
        schema="procurement",
    )
    op.create_index("ix_vendors_tenant_id", "vendors", ["tenant_id"], schema="procurement")
    op.create_index("ix_vendors_status", "vendors", ["status"], schema="procurement")
    op.create_index("ix_vendors_risk_status", "vendors", ["risk_status"], schema="procurement")
    op.create_index("ix_vendors_tax_identifier", "vendors", ["tax_identifier"], schema="procurement")
    op.create_index("ix_vendors_legal_name", "vendors", ["legal_name"], schema="procurement")

    # 8. procurement.purchase_orders
    op.create_table(
        "purchase_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement.vendors.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("po_number", sa.String(50), nullable=False),
        sa.Column("po_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(50), nullable=False, server_default="DRAFT"),
        sa.Column("approval_status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("subtotal", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("tax_total", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("discount_total", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("grand_total", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "po_number", name="uq_purchase_orders_tenant_po_number"),
        sa.CheckConstraint("subtotal >= 0", name="ck_purchase_orders_subtotal_positive"),
        sa.CheckConstraint("tax_total >= 0", name="ck_purchase_orders_tax_total_positive"),
        sa.CheckConstraint("discount_total >= 0", name="ck_purchase_orders_discount_total_positive"),
        sa.CheckConstraint("grand_total >= 0", name="ck_purchase_orders_grand_total_positive"),
        schema="procurement",
    )
    op.create_index("ix_purchase_orders_tenant_id", "purchase_orders", ["tenant_id"], schema="procurement")
    op.create_index("ix_purchase_orders_vendor_id", "purchase_orders", ["vendor_id"], schema="procurement")
    op.create_index("ix_purchase_orders_po_number", "purchase_orders", ["po_number"], schema="procurement")
    op.create_index("ix_purchase_orders_status", "purchase_orders", ["status"], schema="procurement")
    op.create_index("ix_purchase_orders_po_date", "purchase_orders", ["po_date"], schema="procurement")

    # 9. procurement.purchase_order_items
    op.create_table(
        "purchase_order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement.purchase_orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("product_code", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_of_measure", sa.String(20), nullable=False, server_default="EA"),
        sa.Column("unit_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("tax_rate", sa.Numeric(8, 4), nullable=False, server_default="0.0000"),
        sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("line_total", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("purchase_order_id", "line_number", name="uq_po_items_po_line_number"),
        sa.CheckConstraint("quantity > 0", name="ck_po_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_po_items_unit_price_positive"),
        sa.CheckConstraint("tax_rate >= 0", name="ck_po_items_tax_rate_positive"),
        sa.CheckConstraint("discount_amount >= 0", name="ck_po_items_discount_positive"),
        sa.CheckConstraint("line_total >= 0", name="ck_po_items_line_total_positive"),
        schema="procurement",
    )
    op.create_index("ix_po_items_tenant_id", "purchase_order_items", ["tenant_id"], schema="procurement")
    op.create_index("ix_po_items_purchase_order_id", "purchase_order_items", ["purchase_order_id"], schema="procurement")

    # 10. procurement.goods_receipts
    op.create_table(
        "goods_receipts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement.purchase_orders.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("receipt_number", sa.String(50), nullable=False),
        sa.Column("received_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACCEPTED"),
        sa.Column("received_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "receipt_number", name="uq_goods_receipts_tenant_receipt_number"),
        schema="procurement",
    )
    op.create_index("ix_goods_receipts_tenant_id", "goods_receipts", ["tenant_id"], schema="procurement")
    op.create_index("ix_goods_receipts_purchase_order_id", "goods_receipts", ["purchase_order_id"], schema="procurement")
    op.create_index("ix_goods_receipts_status", "goods_receipts", ["status"], schema="procurement")

    # 11. procurement.goods_receipt_items
    op.create_table(
        "goods_receipt_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("goods_receipt_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement.goods_receipts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("purchase_order_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement.purchase_order_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("received_quantity", sa.Numeric(18, 4), nullable=False, server_default="0.0000"),
        sa.Column("accepted_quantity", sa.Numeric(18, 4), nullable=False, server_default="0.0000"),
        sa.Column("rejected_quantity", sa.Numeric(18, 4), nullable=False, server_default="0.0000"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("received_quantity >= 0", name="ck_gr_items_received_qty_positive"),
        sa.CheckConstraint("accepted_quantity >= 0", name="ck_gr_items_accepted_qty_positive"),
        sa.CheckConstraint("rejected_quantity >= 0", name="ck_gr_items_rejected_qty_positive"),
        sa.CheckConstraint("accepted_quantity + rejected_quantity <= received_quantity", name="ck_gr_items_accepted_plus_rejected_lte_received"),
        schema="procurement",
    )
    op.create_index("ix_gr_items_tenant_id", "goods_receipt_items", ["tenant_id"], schema="procurement")
    op.create_index("ix_gr_items_goods_receipt_id", "goods_receipt_items", ["goods_receipt_id"], schema="procurement")
    op.create_index("ix_gr_items_po_item_id", "goods_receipt_items", ["purchase_order_item_id"], schema="procurement")

    # 12. ap.invoices
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement.vendors.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("purchase_order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement.purchase_orders.id", ondelete="SET NULL"), nullable=True),
        sa.Column("invoice_number", sa.String(50), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(50), nullable=False, server_default="RECEIVED"),
        sa.Column("current_revision_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="UPLOAD"),
        sa.Column("source_file_name", sa.String(255), nullable=True),
        sa.Column("source_file_url", sa.Text(), nullable=True),
        sa.Column("document_hash", sa.String(64), nullable=True),
        sa.Column("extraction_status", sa.String(50), nullable=False, server_default="NOT_STARTED"),
        sa.Column("extraction_confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "vendor_id", "invoice_number", name="uq_invoices_tenant_vendor_invoice_num"),
        schema="ap",
    )
    op.create_index("ix_invoices_tenant_id", "invoices", ["tenant_id"], schema="ap")
    op.create_index("ix_invoices_vendor_id", "invoices", ["vendor_id"], schema="ap")
    op.create_index("ix_invoices_po_id", "invoices", ["purchase_order_id"], schema="ap")
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"], schema="ap")
    op.create_index("ix_invoices_status", "invoices", ["status"], schema="ap")
    op.create_index("ix_invoices_due_date", "invoices", ["due_date"], schema="ap")
    op.create_index("ix_invoices_document_hash", "invoices", ["document_hash"], schema="ap")
    op.create_index("ix_invoices_created_at", "invoices", ["created_at"], schema="ap")

    # 13. ap.invoice_revisions
    op.create_table(
        "invoice_revisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("invoice_number", sa.String(50), nullable=False),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("subtotal", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("discount_total", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("tax_total", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("grand_total", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("vendor_name_as_submitted", sa.String(255), nullable=True),
        sa.Column("vendor_tax_id_as_submitted", sa.String(50), nullable=True),
        sa.Column("bank_account_last4", sa.String(4), nullable=True),
        sa.Column("bank_account_hash", sa.String(64), nullable=True),
        sa.Column("extraction_method", sa.String(50), nullable=True),
        sa.Column("extraction_confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("raw_extracted_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("submitted_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("invoice_id", "revision_number", name="uq_invoice_revisions_invoice_rev_num"),
        sa.CheckConstraint("subtotal >= 0", name="ck_invoice_rev_subtotal_positive"),
        sa.CheckConstraint("tax_total >= 0", name="ck_invoice_rev_tax_total_positive"),
        sa.CheckConstraint("discount_total >= 0", name="ck_invoice_rev_discount_positive"),
        sa.CheckConstraint("grand_total >= 0", name="ck_invoice_rev_grand_total_positive"),
        schema="ap",
    )
    op.create_index("ix_invoice_revisions_tenant_id", "invoice_revisions", ["tenant_id"], schema="ap")
    op.create_index("ix_invoice_revisions_invoice_id", "invoice_revisions", ["invoice_id"], schema="ap")
    op.create_index("ix_invoice_revisions_invoice_number", "invoice_revisions", ["invoice_number"], schema="ap")

    # Add foreign key for current_revision_id on ap.invoices
    op.create_foreign_key(
        "fk_invoices_current_revision_id",
        "invoices",
        "invoice_revisions",
        ["current_revision_id"],
        ["id"],
        source_schema="ap",
        referent_schema="ap",
        ondelete="SET NULL",
    )

    # 14. ap.invoice_items
    op.create_table(
        "invoice_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoice_revisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("product_code", sa.String(50), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False),
        sa.Column("unit_of_measure", sa.String(20), nullable=False, server_default="EA"),
        sa.Column("unit_price", sa.Numeric(18, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("tax_rate", sa.Numeric(8, 4), nullable=False, server_default="0.0000"),
        sa.Column("tax_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("line_total", sa.Numeric(18, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("invoice_revision_id", "line_number", name="uq_invoice_items_rev_line_number"),
        sa.CheckConstraint("quantity > 0", name="ck_invoice_items_quantity_positive"),
        sa.CheckConstraint("unit_price >= 0", name="ck_invoice_items_unit_price_positive"),
        sa.CheckConstraint("tax_rate >= 0", name="ck_invoice_items_tax_rate_positive"),
        sa.CheckConstraint("discount_amount >= 0", name="ck_invoice_items_discount_positive"),
        sa.CheckConstraint("line_total >= 0", name="ck_invoice_items_line_total_positive"),
        schema="ap",
    )
    op.create_index("ix_invoice_items_tenant_id", "invoice_items", ["tenant_id"], schema="ap")
    op.create_index("ix_invoice_items_revision_id", "invoice_items", ["invoice_revision_id"], schema="ap")

    # 15. ap.control_runs
    op.create_table(
        "control_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoice_revisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("run_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(50), nullable=False, server_default="RUNNING"),
        sa.Column("ruleset_version", sa.String(50), nullable=False, server_default="v1.0"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("triggered_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("invoice_revision_id", "run_number", name="uq_control_runs_rev_run_number"),
        schema="ap",
    )
    op.create_index("ix_control_runs_tenant_id", "control_runs", ["tenant_id"], schema="ap")
    op.create_index("ix_control_runs_invoice_id", "control_runs", ["invoice_id"], schema="ap")
    op.create_index("ix_control_runs_revision_id", "control_runs", ["invoice_revision_id"], schema="ap")
    op.create_index("ix_control_runs_status", "control_runs", ["status"], schema="ap")

    # 16. ap.control_results
    op.create_table(
        "control_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("control_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.control_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("control_code", sa.String(50), nullable=False),
        sa.Column("control_category", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("expected_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("actual_value", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("variance_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("variance_percentage", sa.Numeric(8, 4), nullable=True),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("rule_version", sa.String(50), nullable=False, server_default="v1.0"),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("control_run_id", "control_code", name="uq_control_results_run_code"),
        schema="ap",
    )
    op.create_index("ix_control_results_tenant_id", "control_results", ["tenant_id"], schema="ap")
    op.create_index("ix_control_results_run_id", "control_results", ["control_run_id"], schema="ap")
    op.create_index("ix_control_results_invoice_id", "control_results", ["invoice_id"], schema="ap")
    op.create_index("ix_control_results_code", "control_results", ["control_code"], schema="ap")
    op.create_index("ix_control_results_status", "control_results", ["status"], schema="ap")
    op.create_index("ix_control_results_severity", "control_results", ["severity"], schema="ap")

    # 17. ap.risk_signals
    op.create_table(
        "risk_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("control_result_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.control_results.id", ondelete="SET NULL"), nullable=True),
        sa.Column("signal_code", sa.String(50), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("score", sa.Numeric(5, 2), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("evidence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        schema="ap",
    )
    op.create_index("ix_risk_signals_tenant_id", "risk_signals", ["tenant_id"], schema="ap")
    op.create_index("ix_risk_signals_invoice_id", "risk_signals", ["invoice_id"], schema="ap")
    op.create_index("ix_risk_signals_signal_code", "risk_signals", ["signal_code"], schema="ap")
    op.create_index("ix_risk_signals_category", "risk_signals", ["category"], schema="ap")
    op.create_index("ix_risk_signals_severity", "risk_signals", ["severity"], schema="ap")
    op.create_index("ix_risk_signals_status", "risk_signals", ["status"], schema="ap")

    # 18. ap.exceptions
    op.create_table(
        "exceptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("control_result_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.control_results.id", ondelete="SET NULL"), nullable=True),
        sa.Column("exception_code", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="OPEN"),
        sa.Column("assigned_to", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolution", sa.Text(), nullable=True),
        sa.Column("resolved_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="ap",
    )
    op.create_index("ix_exceptions_tenant_id", "exceptions", ["tenant_id"], schema="ap")
    op.create_index("ix_exceptions_invoice_id", "exceptions", ["invoice_id"], schema="ap")
    op.create_index("ix_exceptions_code", "exceptions", ["exception_code"], schema="ap")
    op.create_index("ix_exceptions_severity", "exceptions", ["severity"], schema="ap")
    op.create_index("ix_exceptions_status", "exceptions", ["status"], schema="ap")
    op.create_index("ix_exceptions_assigned_to", "exceptions", ["assigned_to"], schema="ap")

    # 19. ap.approval_policies
    op.create_table(
        "approval_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("min_amount", sa.Numeric(18, 2), nullable=False, server_default="0.00"),
        sa.Column("max_amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("required_role", sa.String(50), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("requires_all_controls_pass", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("min_amount >= 0", name="ck_approval_policies_min_amount_positive"),
        schema="ap",
    )
    op.create_index("ix_approval_policies_tenant_id", "approval_policies", ["tenant_id"], schema="ap")
    op.create_index("ix_approval_policies_active", "approval_policies", ["active"], schema="ap")

    # 20. ap.approvals
    op.create_table(
        "approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("approval_policy_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.approval_policies.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("approver_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(50), nullable=False, server_default="PENDING"),
        sa.Column("decision", sa.String(50), nullable=True),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("invoice_id", "sequence_order", name="uq_approvals_invoice_seq"),
        schema="ap",
    )
    op.create_index("ix_approvals_tenant_id", "approvals", ["tenant_id"], schema="ap")
    op.create_index("ix_approvals_invoice_id", "approvals", ["invoice_id"], schema="ap")
    op.create_index("ix_approvals_approver_id", "approvals", ["approver_user_id"], schema="ap")
    op.create_index("ix_approvals_status", "approvals", ["status"], schema="ap")

    # 21. ap.payable_ledger
    op.create_table(
        "payable_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoices.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("invoice_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoice_revisions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("vendor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("procurement.vendors.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("payable_number", sa.String(50), nullable=False),
        sa.Column("approved_amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="OPEN"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "invoice_id", name="uq_payable_ledger_tenant_invoice"),
        sa.UniqueConstraint("tenant_id", "payable_number", name="uq_payable_ledger_tenant_payable_num"),
        sa.CheckConstraint("approved_amount > 0", name="ck_payable_ledger_approved_amount_positive"),
        schema="ap",
    )
    op.create_index("ix_payable_ledger_tenant_id", "payable_ledger", ["tenant_id"], schema="ap")
    op.create_index("ix_payable_ledger_vendor_id", "payable_ledger", ["vendor_id"], schema="ap")
    op.create_index("ix_payable_ledger_status", "payable_ledger", ["status"], schema="ap")
    op.create_index("ix_payable_ledger_due_date", "payable_ledger", ["due_date"], schema="ap")
    op.create_index("ix_payable_ledger_payable_number", "payable_ledger", ["payable_number"], schema="ap")

    # 22. ap.payments
    op.create_table(
        "payments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("payable_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.payable_ledger.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("payment_reference", sa.String(100), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="INR"),
        sa.Column("status", sa.String(50), nullable=False, server_default="SCHEDULED"),
        sa.Column("payment_method", sa.String(50), nullable=False, server_default="NEFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("tenant_id", "payment_reference", name="uq_payments_tenant_payment_ref"),
        sa.CheckConstraint("amount > 0", name="ck_payments_amount_positive"),
        schema="ap",
    )
    op.create_index("ix_payments_tenant_id", "payments", ["tenant_id"], schema="ap")
    op.create_index("ix_payments_payable_id", "payments", ["payable_id"], schema="ap")
    op.create_index("ix_payments_status", "payments", ["status"], schema="ap")
    op.create_index("ix_payments_payment_date", "payments", ["payment_date"], schema="ap")

    # 23. ap.invoice_embeddings
    op.create_table(
        "invoice_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoice_revisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("source_text_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="ap",
    )
    op.create_index("ix_invoice_embeddings_tenant_id", "invoice_embeddings", ["tenant_id"], schema="ap")
    op.create_index("ix_invoice_embeddings_invoice_id", "invoice_embeddings", ["invoice_id"], schema="ap")
    op.create_index("ix_invoice_embeddings_revision_id", "invoice_embeddings", ["invoice_revision_id"], schema="ap")

    # 24. audit.audit_logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", sa.String(100), nullable=True),
        sa.Column("correlation_id", sa.String(100), nullable=True),
        sa.Column("previous_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("new_state", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="audit",
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"], schema="audit")
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_user_id"], schema="audit")
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], schema="audit")
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"], schema="audit")
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"], schema="audit")
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"], schema="audit")

    # 25. Append-only trigger on audit.audit_logs
    op.execute("""
    CREATE OR REPLACE FUNCTION audit.prevent_audit_log_modification()
    RETURNS TRIGGER AS $$
    BEGIN
        RAISE EXCEPTION 'audit.audit_logs is append-only. Modification and deletion are strictly forbidden.';
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER trg_prevent_audit_log_modification
    BEFORE UPDATE OR DELETE ON audit.audit_logs
    FOR EACH ROW
    EXECUTE FUNCTION audit.prevent_audit_log_modification();
    """)

def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_audit_log_modification ON audit.audit_logs")
    op.execute("DROP FUNCTION IF EXISTS audit.prevent_audit_log_modification()")
    
    op.drop_table("audit_logs", schema="audit")
    op.drop_table("invoice_embeddings", schema="ap")
    op.drop_table("payments", schema="ap")
    op.drop_table("payable_ledger", schema="ap")
    op.drop_table("approvals", schema="ap")
    op.drop_table("approval_policies", schema="ap")
    op.drop_table("exceptions", schema="ap")
    op.drop_table("risk_signals", schema="ap")
    op.drop_table("control_results", schema="ap")
    op.drop_table("control_runs", schema="ap")
    op.drop_table("invoice_items", schema="ap")
    
    # Drop circular foreign key before dropping invoices
    op.drop_constraint("fk_invoices_current_revision_id", "invoices", schema="ap", type_="foreignkey")
    op.drop_table("invoice_revisions", schema="ap")
    op.drop_table("invoices", schema="ap")
    
    op.drop_table("goods_receipt_items", schema="procurement")
    op.drop_table("goods_receipts", schema="procurement")
    op.drop_table("purchase_order_items", schema="procurement")
    op.drop_table("purchase_orders", schema="procurement")
    op.drop_table("vendors", schema="procurement")
    
    op.drop_table("user_roles", schema="identity")
    op.drop_table("roles", schema="identity")
    op.drop_table("users", schema="identity")
    op.drop_table("tenants", schema="identity")
    
    op.execute("DROP SCHEMA IF EXISTS audit CASCADE")
    op.execute("DROP SCHEMA IF EXISTS ap CASCADE")
    op.execute("DROP SCHEMA IF EXISTS procurement CASCADE")
    op.execute("DROP SCHEMA IF EXISTS identity CASCADE")
