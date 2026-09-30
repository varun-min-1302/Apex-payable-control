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

## 🏛️ Platform Architecture & Technology Stack

| Layer | Technology | Key Capabilities & Deliverables |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS | Polished fintech SaaS interface, left navigation sidebar, 7 Finathon persona switcher, 3-Way Match inspector, exception resolution, approval sign-off, general liability ledger. |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2 | 25+ REST endpoints (`/api/v1`), OpenAPI Swagger docs, JWT bearer auth with Finathon demo role emulation, **The Golden Transaction**. |
| **Database** | PostgreSQL 16+ (Supabase / Local), Alembic, pgvector | Multi-tenant schema (`identity`, `procurement`, `ap`, `audit`), 22 relational tables, strict `NUMERIC(18,2)` financial types, and immutable append-only triggers. |
| **AI Extraction** | Google Gemini API (`google-genai` SDK) | Multimodal invoice parsing (PDF & images), structured Pydantic extraction with fallback to deterministic mock provider. |
| **Deployment** | Vercel (Frontend) + Render (Backend) + Supabase (Database) | Serverless frontend SPA hosting with global CDN, containerized Python web service, and managed cloud PostgreSQL. |

---

## 🎨 Frontend Design & Visual Language

- **Navigation Sidebar**: Clean, structured access to all operational views (`Overview`, `Invoices`, `Needs Attention`, `Approvals`, `Payments`, `Vendors & Orders`), testing tools (`Control Simulator`, `Finathon Scenarios`, `Audit Activity`), system health indicator (`● System operational`), Theme switcher (Light/Dark), and active Persona Switcher.
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

## 🚀 Local Development Quickstart

### Prerequisites
- Python 3.11+
- Node.js 18+ & npm
- PostgreSQL 16+ (or remote Supabase connection)

### 1. Backend Setup
```bash
# Clone the repository
git clone https://github.com/varun-min-1302/Apex-payable-control.git
cd Apex-payable-control

# Create virtual environment & install dependencies
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your local PostgreSQL or Supabase credentials
```

### 2. Run Database Migrations & Seed Demo Data
```bash
# Apply Alembic schema migrations (22 tables)
alembic -c backend/alembic.ini upgrade head

# Seed 7 demo personas and 15 benchmark scenarios
python -m scripts.seed_demo_data
python -m scripts.seed_finathon_scenarios
```

### 3. Start Backend Server
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- API Health Check: [http://localhost:8000/health](http://localhost:8000/health)
- Interactive Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
- Application UI: [http://localhost:5173](http://localhost:5173)

---

## ☁️ Cloud Deployment Guide (Supabase + Render + Vercel)

### Step 1: Database Setup (Supabase PostgreSQL)
1. Create a project at [supabase.com](https://supabase.com).
2. Under **Project Settings -> Database**, copy the **URI** connection string (select **Session pooler** or **Direct connection** with `sslmode=require`).
3. Set your connection string in your backend environment:
   ```env
   DATABASE_URL=postgresql+psycopg2://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require
   ```
4. Run migrations from your local terminal against Supabase:
   ```bash
   alembic -c backend/alembic.ini upgrade head
   python -m scripts.seed_demo_data
   python -m scripts.seed_finathon_scenarios
   ```

### Step 2: Backend Deployment (Render)
1. Create a new **Web Service** on [render.com](https://render.com) connected to your GitHub repository.
2. Select **Python 3** runtime with the following configuration:
   - **Root Directory:** *(leave blank)*
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
3. Configure Environment Variables in Render:
   - `DATABASE_URL`: Your Supabase connection string.
   - `GEMINI_API_KEY`: Your Gemini API key from AI Studio.
   - `GEMINI_MODEL`: `gemini-2.5-flash`
   - `EXTRACTION_PROVIDER`: `gemini` (or `mock`)
   - `STORAGE_ROOT_DIR`: `/tmp/storage`
   - `ALLOWED_ORIGINS`: `https://your-frontend.vercel.app` (or leave empty to allow all Vercel preview domains).
4. Deploy and verify health at: `https://[your-service].onrender.com/health`

*(A preconfigured `render.yaml` Blueprint is provided in the repository for 1-click Render deployment).*

### Step 3: Frontend Deployment (Vercel)
1. Import the repository on [vercel.com](https://vercel.com).
2. Configure Project Settings:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
3. Add Environment Variable:
   - `VITE_API_URL`: `https://[your-service].onrender.com` (no trailing slash)
4. Deploy! The included `frontend/vercel.json` automatically configures SPA client-side routing.

---

## 🧪 Verification & Automated Testing

Run the full automated test suite (186 unit, integration, and scenario tests):

```bash
# Run backend pytest suite
python -m pytest backend/tests/ -v

# Verify frontend production build
cd frontend
npm run build
```

---

## 🔒 Security & Data Integrity Principles

- **No Hardcoded Secrets**: All credentials, database URIs, and Gemini API keys are loaded strictly from environment variables.
- **Append-Only Immutable Audit Trail**: All state mutations generate hash-chained structured audit logs backed by PostgreSQL trigger constraints prohibiting `UPDATE` or `DELETE` on the `audit.audit_logs` table.
- **Tenant Isolation**: Every database entity enforces tenant UUID foreign keys and unique constraints preventing cross-tenant leakage.
- **Financial Precision**: All monetary values are strictly stored as `NUMERIC(18,2)` (never floating point).

---

## 📜 License
Built for the Finathon Hackathon. All rights reserved.
