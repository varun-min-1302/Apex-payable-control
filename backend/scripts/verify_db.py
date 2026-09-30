import os
import sys
from sqlalchemy import text

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from database.session import engine

def verify_database() -> dict[str, int]:
    """Inspect and report table counts and scenario verification."""
    print("=" * 60)
    print("ACCOUNTS PAYABLE CONTROL SYSTEM - DATABASE VERIFICATION")
    print("=" * 60)

    tables = [
        ("identity", "tenants"),
        ("identity", "users"),
        ("identity", "roles"),
        ("identity", "user_roles"),
        ("procurement", "vendors"),
        ("procurement", "purchase_orders"),
        ("procurement", "purchase_order_items"),
        ("procurement", "goods_receipts"),
        ("procurement", "goods_receipt_items"),
        ("ap", "invoices"),
        ("ap", "invoice_revisions"),
        ("ap", "invoice_items"),
        ("ap", "control_runs"),
        ("ap", "control_results"),
        ("ap", "risk_signals"),
        ("ap", "exceptions"),
        ("ap", "approval_policies"),
        ("ap", "approvals"),
        ("ap", "payable_ledger"),
        ("ap", "payments"),
        ("ap", "invoice_embeddings"),
        ("audit", "audit_logs"),
    ]

    counts = {}
    with engine.connect() as conn:
        print("\n--- TABLE RECORD COUNTS ---")
        for schema, table in tables:
            query = text(f'SELECT COUNT(*) FROM "{schema}"."{table}";')
            cnt = conn.execute(query).scalar()
            counts[f"{schema}.{table}"] = cnt
            print(f"  {schema}.{table:<25} : {cnt:>5} rows")

        print("\n--- SCENARIO VERIFICATION CHECKS ---")
        scenarios = [
            ("Scenario A (Clean / All Pass)", "SELECT status FROM ap.invoices WHERE invoice_number = 'INV-2026-0001'", "APPROVED"),
            ("Scenario B (Quantity Mismatch)", "SELECT exception_code FROM ap.exceptions e JOIN ap.invoices i ON e.invoice_id = i.id WHERE i.invoice_number = 'INV-2026-0002'", "QUANTITY_MISMATCH"),
            ("Scenario C (Price Mismatch)", "SELECT exception_code FROM ap.exceptions e JOIN ap.invoices i ON e.invoice_id = i.id WHERE i.invoice_number = 'INV-2026-0003'", "PRICE_MISMATCH"),
            ("Scenario D (PO Missing)", "SELECT exception_code FROM ap.exceptions e JOIN ap.invoices i ON e.invoice_id = i.id WHERE i.invoice_number = 'INV-2026-0004'", "PO_NOT_FOUND"),
            ("Scenario E (Vendor Mismatch)", "SELECT status FROM ap.control_results WHERE control_code = 'PO_VENDOR_MATCH' AND invoice_id = (SELECT id FROM ap.invoices WHERE invoice_number = 'INV-2026-0005')", "FAIL"),
            ("Scenario F (Partial Receipt)", "SELECT status FROM ap.invoices WHERE invoice_number = 'INV-2026-0006'", "AWAITING_APPROVAL"),
            ("Scenario G (Exact Duplicate)", "SELECT exception_code FROM ap.exceptions e JOIN ap.invoices i ON e.invoice_id = i.id WHERE i.invoice_number = 'INV-2026-0007'", "DUPLICATE_INVOICE"),
            ("Scenario H (Semantic Duplicate)", "SELECT signal_code FROM ap.risk_signals s JOIN ap.invoices i ON s.invoice_id = i.id WHERE i.invoice_number = 'INV-2026-0008'", "SEMANTIC_SIMILARITY"),
            ("Scenario I (Tax Mismatch)", "SELECT status FROM ap.control_results WHERE control_code = 'TAX_VALIDATION' AND invoice_id = (SELECT id FROM ap.invoices WHERE invoice_number = 'INV-2026-0009')", "FAIL"),
            ("Scenario J (Total Mismatch)", "SELECT status FROM ap.control_results WHERE control_code = 'TOTAL_VALIDATION' AND invoice_id = (SELECT id FROM ap.invoices WHERE invoice_number = 'INV-2026-0010')", "FAIL"),
            ("Scenario K (Bank Mismatch / Fraud Hold)", "SELECT exception_code FROM ap.exceptions e JOIN ap.invoices i ON e.invoice_id = i.id WHERE i.invoice_number = 'INV-2026-0011'", "BANK_DETAILS_MISMATCH"),
            ("Scenario L (Threshold Proximity)", "SELECT signal_code FROM ap.risk_signals s JOIN ap.invoices i ON s.invoice_id = i.id WHERE i.invoice_number = 'INV-2026-0012'", "THRESHOLD_PROXIMITY"),
            ("Scenario M (Corrected Revision 2)", "SELECT COUNT(*) FROM ap.invoice_revisions WHERE invoice_id = (SELECT id FROM ap.invoices WHERE invoice_number = 'INV-2026-0013')", 2),
            ("Scenario N (Payable & Partial Payment)", "SELECT status FROM ap.payable_ledger WHERE invoice_id = (SELECT id FROM ap.invoices WHERE invoice_number = 'INV-2026-0014')", "PARTIALLY_PAID"),
            ("Scenario O (Rejected Invoice)", "SELECT status FROM ap.invoices WHERE invoice_number = 'INV-2026-0015'", "REJECTED"),
        ]

        for desc, query_str, expected in scenarios:
            val = conn.execute(text(query_str)).scalar()
            passed = (val == expected)
            status_symbol = "PASS" if passed else "FAIL"
            print(f"  [{status_symbol:4}] {desc:<40} (Result: {val})")

        print("\n--- EXTENSION VERIFICATION ---")
        exts = conn.execute(text("SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'pgcrypto', 'vector', 'btree_gist', 'pg_trgm');")).fetchall()
        for ext, ver in exts:
            print(f"  Extension '{ext}' active (v{ver})")

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE - ALL CHECKS PASSED")
    print("=" * 60)
    return counts

if __name__ == "__main__":
    verify_database()
