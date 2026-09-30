"""Add invoice_documents table for invoice intake and secure document storage

Revision ID: 0002_invoice_documents
Revises: 0001_initial_schema
Create Date: 2026-09-30 19:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_invoice_documents"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "invoice_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ap.invoices.id", ondelete="SET NULL"), nullable=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("sanitized_filename", sa.String(255), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256_hash", sa.String(64), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="UPLOAD"),
        sa.Column("status", sa.String(50), nullable=False, server_default="READY_FOR_EXTRACTION"),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("identity.users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        schema="ap",
    )
    op.create_index("ix_invoice_documents_tenant_id", "invoice_documents", ["tenant_id"], schema="ap")
    op.create_index("ix_invoice_documents_invoice_id", "invoice_documents", ["invoice_id"], schema="ap")
    op.create_index("ix_invoice_documents_sha256_hash", "invoice_documents", ["sha256_hash"], schema="ap")
    op.create_index("ix_invoice_documents_tenant_hash", "invoice_documents", ["tenant_id", "sha256_hash"], schema="ap")
    op.create_index("ix_invoice_documents_created_at", "invoice_documents", ["created_at"], schema="ap")

def downgrade() -> None:
    op.drop_table("invoice_documents", schema="ap")
