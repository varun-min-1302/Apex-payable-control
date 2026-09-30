# Enterprise Accounts Payable Control System (Finathon)

A production-grade, enterprise Accounts Payable (AP) Control & Fraud Prevention Platform designed around the core principle:

$$\mathbf{RECEIVED\ INVOICE \ne PAYABLE\ OBLIGATION}$$

An uploaded or extracted invoice **never** automatically creates a payable obligation. Every invoice must pass deterministic controls (3-way matching, duplicate detection, tax validation, mathematical proof, bank fingerprinting) and authority-governed approval workflows before entering the payable ledger.

---

## Platform Architecture & Implementation Status

The platform is designed and fully implemented across 4 cohesive enterprise layers:

| Layer | Technology | Key Deliverables & Capabilities |
| :--- | :--- | :--- |
| **Phase 1: Database Foundation** | PostgreSQL 16+, Alembic, pgvector | Multi-tenant schema (`identity`, `procurement`, `ap`, `audit`), 22 tables, strict `NUMERIC(18,2)` financials, immutable audit triggers. |
| **Phase 2: Deterministic Control Engine** | Python 3.12, SQLAlchemy 2 | 18 explainable controls across Vendor, PO, Receipt, Financials, Duplicates, and Risk Signals. Single-query context builder. |
| **Phase 3: Enterprise REST API** | FastAPI, Pydantic v2, Uvicorn | 25+ REST endpoints (`/api/v1`), OpenAPI Swagger docs, JWT bearer auth with Finathon demo role emulation, **The Golden Transaction**. |
| **Phase 4: Responsive Frontend** | React 19, TypeScript, Vite, Tailwind CSS | High-trust financial cockpit, 7 Finathon persona switcher, 3-Way Match inspector, exception resolution, approval sign-off, general liability ledger. |

---

## Live System URLs

When running locally:
- **Web Application Cockpit:** [http://localhost:5173](http://localhost:5173)
- **Interactive Swagger Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Reference:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Direct Backend Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## Finathon Demo Personas (Role-Based Testing)

The frontend features a 1-click **Persona Switcher** in the top navigation bar, dynamically passing the `X-Demo-User-Email` header to demonstrate real-time role-based access control (RBAC):

| Persona Name | Email | Role | Permitted Capabilities & Scenarios |
| :--- | :--- | :--- | :--- |
| **Rajesh Sharma** | `rajesh.sharma@apexfin.in` | `ADMIN` | Unrestricted access across all modules, controls re-run, overrides, and CFO-level sign-offs (> ₹2.5M). |
| **Priya Nair** | `priya.nair@apexfin.in` | `AP_CLERK` | Invoice intake/creation, line item corrections, Tier 1 approvals (up to ₹50,000). |
| **Vikram Malhotra** | `vikram.malhotra@apexfin.in` | `PROCUREMENT_MANAGER` | Purchase order management, pricing exception resolution, PO variance investigations. |
| **Sneha Kulkarni** | `sneha.kulkarni@apexfin.in` | `RECEIVING_USER` | Goods receipts inspection, receiving logs, quantity mismatch resolution. |
| **Ananya Rao** | `ananya.rao@apexfin.in` | `FINANCE_MANAGER` | Exception waivers, Tier 2 approvals (₹50k - ₹500k), disbursement execution. |
| **Rohan Verma** | `rohan.verma@apexfin.in` | `FINANCE_HEAD` | Executive Tier 3 approvals (₹500k - ₹2.5M), policy overrides, payment authorizer. |
| **Sunita Mehta** | `sunita.mehta@apexfin.in` | `AUDITOR` | Immutable append-only audit trail inspection, control run forensic verification (Read-Only). |

---

## Core Frontend Views

1. **Dashboard Overview (`/`)**:
   - Executive financial KPIs: Total Invoices, Awaiting Approval, Open Exceptions, Active Liability, Total Disbursed, and 3-Way Match Pass Rate (%).
   - **Deliberate Scenarios Matrix (A through O)**: 15 benchmark invoices demonstrating clean matches, quantity variances, price mismatches, missing POs, duplicate submissions, tax calculation errors, and bank account changes.
2. **Invoices Hub (`/invoices`)**:
   - Multi-status filter tabs (`ALL`, `AWAITING_APPROVAL`, `EXCEPTION`, `APPROVED`, `PAYABLE_CREATED`, `PAID`, `REJECTED`).
   - Real-time search across invoice numbers and vendor legal names.
   - **New Invoice Intake Modal**: Submit new invoice shells with line items directly into intake status (`RECEIVED`).
3. **3-Way Match Inspector Modal**:
   - Comprehensive side-by-side reconciliation: Invoice vs Purchase Order vs Goods Receipt.
   - Detailed breakdown of all 18 deterministic control checks with expected values, actual values, variances, severity, and rule versions.
   - Live **"Re-run Control Engine"** button to execute controls on-demand.
4. **Exceptions Management (`/exceptions`)**:
   - Central triage inbox for price mismatches, quantity discrepancies, duplicate warnings, and bank holds.
   - **Mandatory Audit Resolution Modal**: Resolving or waiving an exception strictly requires a justification reason logged to the immutable audit trail.
5. **Approval Workflow & The Golden Transaction (`/approvals`)**:
   - Authority-filtered pending sign-off queue based on the active persona's role tier.
   - **The Golden Transaction**: Approving the final checkpoint atomically commits the invoice to the `ap.payable_ledger` with an official `PAY-2026-XXXX` obligation number.
6. **Payable Ledger & Disbursements (`/payables`)**:
   - General liability ledger tracking approved obligations, due dates, paid amounts, and remaining balances.
   - **Record Disbursement Modal**: Execute partial or full financial disbursements (`NEFT`, `RTGS`, `ACH`) with transaction reference tracking.
7. **Procurement Directory (`/procurement`)**:
   - Tabbed master views for Vendors (with masked bank accounts and SHA-256 hashes), Purchase Orders, and Warehouse Goods Receipts.
8. **Append-Only Audit Trail (`/audit`)**:
   - Immutable audit event explorer with interactive previous/new JSON state diffs and correlation tracking.

---

## How to Run Concurrently

### 1. Start PostgreSQL 16
```powershell
& "D:\pgsql16\pgsql\bin\postgres.exe" -D "d:\pgsql16\data"
```

### 2. Start FastAPI Backend (Port 8000)
```powershell
$env:PYTHONPATH="d:\Projects\PA control"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Start Vite Frontend (Port 5173)
```powershell
cd frontend
npm run dev -- --host 0.0.0.0 --port 5173
```

---

## Quick Navigation

- [01 PRD (Product Requirements Document)](file:///d:/Projects/PA%20control/01_PRD.md)
- [02 SRS (Software Requirements Specification)](file:///d:/Projects/PA%20control/02_SRS.md)
- [04 Architecture Specification](file:///d:/Projects/PA%20control/04_Architecture.md)
- [08 Backend Schema & Architecture](file:///d:/Projects/PA%20control/08_Backend_Schema_and_Architecture.md)
- [Backend Implementation README](file:///d:/Projects/PA%20control/backend/README.md)
- [Frontend Package Configuration](file:///d:/Projects/PA%20control/frontend/package.json)
