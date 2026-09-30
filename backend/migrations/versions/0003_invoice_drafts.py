"""Add invoice_drafts table for Phase 5B AI invoice extraction and draft review

Revision ID: 0003_invoice_drafts
Revises: 0002_invoice_documents
Create Date: 2026-09-30 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_invoice_drafts"
down_revision: Union[str, None] = "0002_invoice_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "invoice_drafts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoice_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="EXTRACTED"),
        sa.Column("extracted_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("field_confidences", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("overall_confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("warnings", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("vendor_match", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("confirmed_invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="ap",
    )
    op.create_index("ix_invoice_drafts_tenant_id", "invoice_drafts", ["tenant_id"], schema="ap")
    op.create_index("ix_invoice_drafts_document_id", "invoice_drafts", ["document_id"], schema="ap")
    op.create_index("ix_invoice_drafts_status", "invoice_drafts", ["status"], schema="ap")
    op.create_index("ix_invoice_drafts_confirmed_invoice_id", "invoice_drafts", ["confirmed_invoice_id"], schema="ap")
    op.create_index("ix_invoice_drafts_created_at", "invoice_drafts", ["created_at"], schema="ap")

def downgrade() -> None:
    op.drop_table("invoice_drafts", schema="ap")
