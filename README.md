# Apex Payables — Accounts Payable Control Center
### Apex FinTech Technologies

A production-grade, enterprise Accounts Payable (AP) Control & Fraud Prevention Platform designed around the core principle:

$$\mathbf{RECEIVED\ INVOICE \ne PAYABLE\ OBLIGATION}$$

An uploaded or extracted invoice **never** automatically creates a payable obligation. Every invoice passes deterministic multi-way controls (vendor identity, purchase order reconciliation, goods receipt verification, line-item quantity & price limits, arithmetic totals, tax schedules, duplicate prevention, and risk anomaly detection) and authority-governed approval workflows before entering the payable ledger.

---

## 🎯 The Core Product Story

$$\text{RECEIVE} \longrightarrow \text{UNDERSTAND} \longrightarrow \text{VERIFY} \longrightarrow \text{CONTROL} \longrightarrow \text{APPROVE} \longrightarrow \text{PAY}$$

The primary question throughout the product is:
> **"Can this invoice be paid?"**

The system answers unambiguously with **YES**, **NO**, or **WAITING FOR APPROVAL**, paired with plain-English audit explanations and recommended operational resolutions.

---

## 🏛️ Platform Architecture & Engineering Stack

The system is built across four enterprise layers:

| Layer | Technology | Key Deliverables & Capabilities |
| :--- | :--- | :--- |
| **Phase 1: Database Foundation** | PostgreSQL 16+, Alembic, pgvector | Multi-tenant schema (`identity`, `procurement`, `ap`, `audit`), 22 relational tables, strict `NUMERIC(18,2)` financial types, and immutable append-only triggers. |
| **Phase 2: Deterministic Control Engine** | Python 3.12, SQLAlchemy 2 | 18 explainable controls across Vendor, PO, Receipt, Financials, Duplicates, and Risk Signals. Single-query context builder. |
| **Phase 3: Enterprise REST API** | FastAPI, Pydantic v2, Uvicorn | 25+ REST endpoints (`/api/v1`), OpenAPI Swagger docs, JWT bearer auth with Finathon demo role emulation, **The Golden Transaction**. |
| **Phase 4: Fintech SaaS Cockpit** | React 19, TypeScript, Vite, Tailwind CSS | Polished fintech SaaS interface, left navigation sidebar, 7 Finathon persona switcher, 3-Way Match inspector, exception resolution, approval sign-off, general liability ledger. |

---

## 🎨 Frontend Design & Visual Language

- **Left Navigation Sidebar**: Clean, structured access to all operational views (`Overview`, `Invoices`, `Needs Attention`, `Approvals`, `Payments`, `Vendors & Orders`), testing tools (`Control Simulator`, `Finathon Scenarios`, `Audit Activity`), system health indicator (`● Operational`), Theme switcher (Light/Dark), and active Persona Switcher.
- **Accounts Payable Control Center (Home)**:
  - **Total Payable Liability** balance card with trend throughput and quick ledger actions.
  - **Needs Attention** and **Awaiting Sign-off** triage metrics with direct queue access.
  - **Live Control Workspace**: Interactive operational card demonstrating invoice verification status (`INV-2026-0002` exception vs `INV-2026-0001` clean), 11-step verification pipeline with instant pass/fail indicators, and prominent determination badges (**NOT PAYABLE** / **PAYABLE APPROVED**).
  - **Control Health Micro-Metrics**: Real-time pass rates across Vendor Integrity, Purchase Order, Goods Receipt, Financial & Tax, Duplicate Prevention, and Risk Signals.
  - **Risk Intelligence**: Real-time distribution across Critical, High, Medium, and Low risk tiers with top driver analysis.
- **Invoices Hub**: 4 key financial KPIs (Overdue, Due next month, Avg processing time, Available for payment), multi-status filter tabs, real-time search, and dense fintech rows.
- **Needs Attention (Exception Triage)**: Plain-English explanations ("What happened" and "What to do") with mandatory audit justification modals.
- **Authority Approvals & The Golden Transaction**: Tier-based sign-off authorization (Tiers 1–4) committing approved invoices into official payable obligations (`PAY-2026-XXXX`).
- **Payments & Settlements**: General liability tracking with partial or full disbursements via `NEFT`, `RTGS`, `IMPS`, `UPI`, or `CHEQUE`.
- **Theme Architecture**: Strict semantic design tokens supporting both high-contrast Light Mode and Dark Mode.

---

## 👥 Finathon Demo Personas (Role-Based Access Control)

The frontend features a 1-click **Persona Switcher** in the sidebar, dynamically passing the `X-Demo-User-Email` header to demonstrate real-time role-based access control (RBAC):

| Persona Name | Email | Role | Permitted Capabilities & Scenarios |
| :--- | :--- | :--- | :--- |
| **Rajesh Sharma** | `rajesh.sharma@apexfin.in` | `ADMIN` | Unrestricted access across all modules, controls re-run, overrides, and CFO-level sign-offs (> ₹2.5M). |
| **Priya Nair** | `priya.nair@apexfin.in` | `AP_CLERK` | Invoice intake/creation, line item corrections, Tier 1 approvals (up to ₹50,000). |
| **Vikram Malhotra** | `vikram.malhotra@apexfin.in` | `PROCUREMENT_MANAGER` | Purchase order management, pricing exception resolution, PO variance investigations. |
| **Sneha Kulkarni** | `sneha.kulkarni@apexfin.in` | `RECEIVING_USER` | Goods receipts inspection, receiving logs, quantity mismatch resolution. |
| **Ananya Rao** | `ananya.rao@apexfin.in` | `FINANCE_MANAGER` | Exception waivers, Tier 2 approvals (₹50k – ₹500k), disbursement execution. |
| **Rohan Verma** | `rohan.verma@apexfin.in` | `FINANCE_HEAD` | Executive Tier 3 approvals (₹500k – ₹2.5M), policy overrides, payment authorizer. |
| **Sunita Mehta** | `sunita.mehta@apexfin.in` | `AUDITOR` | Immutable append-only audit trail inspection, forensic verification (Read-Only). |

---

## 🧪 Benchmark Test Scenarios (A through O)

The system includes 15 deliberate seed scenarios accessible under **Finathon Scenarios**:

| Code | Scenario | Triggered Control / Behavior | Expected Determination |
| :--- | :--- | :--- | :--- |
| **A** | Golden Path (Standard) | Clean 3-way match, verified vendor & PO | `PAYABLE_CREATED` |
| **B** | Golden Path (High Value) | Clean 3-way match, amount > ₹1M | `AWAITING_APPROVAL` (Tier 3) |
| **C** | Quantity Discrepancy | Invoice qty (120) > Received qty (100) | `EXCEPTION` (`QUANTITY_MISMATCH`) |
| **D** | Unit Price Variance | Billed unit price > PO unit price | `EXCEPTION` (`PRICE_MISMATCH`) |
| **E** | Missing Goods Receipt | PO exists, goods receipt pending | `EXCEPTION` (`RECEIPT_NOT_FOUND`) |
| **F** | Missing Purchase Order | Non-PO invoice without approved contract | `EXCEPTION` (`PO_NOT_FOUND`) |
| **G** | Exact Duplicate Invoice | Identical vendor, invoice #, and amount | `EXCEPTION` (`DUPLICATE_INVOICE`) |
| **H** | Semantic Duplicate | Different invoice #, identical PO and items | `EXCEPTION` (`POTENTIAL_DUPLICATE`) |
| **I** | Arithmetic Discrepancy | Sum of line items does not equal total | `EXCEPTION` (`ARITHMETIC_ERROR`) |
| **J** | Tax Schedule Variance | Incorrect GST/tax rate applied | `EXCEPTION` (`TAX_MISMATCH`) |
| **K** | Bank Account Mismatch | Remittance account differs from vendor master | `EXCEPTION` (`BANK_DETAILS_MISMATCH`) |
| **L** | Inactive/Suspended Vendor | Vendor state inactive or blacklisted | `EXCEPTION` (`VENDOR_INACTIVE`) |
| **M** | Round Amount Anomaly | Unusually round amount triggering risk signal | `EXCEPTION` (`RISK_SIGNAL`) |
| **N** | Multi-Tier Approval Chain | Invoice requiring sequential sign-offs | `AWAITING_APPROVAL` (Tier 2 → 3) |
| **O** | Disbursed & Settled | Fully authorized invoice disbursed via NEFT | `PAID` |

---

## 🚀 Running Locally

### Prerequisites
- Python 3.12+
- Node.js 18+ & npm
- PostgreSQL 16+

### 1. Start PostgreSQL 16
```powershell
& "D:\pgsql16\pgsql\bin\postgres.exe" -D "d:\pgsql16\data"
```

### 2. Start FastAPI Backend (Port 8000)
```powershell
$env:PYTHONPATH="d:\Projects\PA control"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Start Vite Frontend (Port 5173)
```powershell
cd frontend
npm run dev
```

---

## 🌐 Endpoints & Documentation

- **Web Application Cockpit:** [http://localhost:5173](http://localhost:5173)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Reference:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Backend Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
