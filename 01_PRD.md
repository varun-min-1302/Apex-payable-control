# End-to-End Accounts Payable Control System — Product Requirements Document (PRD)

**Version:** 1.0  
**Status:** Hackathon MVP specification  
**Product Name (working):** AP Control Engine

## 1. Product Summary
AP Control Engine is a finance-control platform that evaluates vendor invoices before they become valid payable obligations. It combines deterministic accounting controls, document extraction, duplicate/similarity detection, workflow routing, human review, a payable ledger, and a tamper-evident audit trail.

Core principle:

> An invoice being received is not the same thing as an invoice being payable.

## 2. Problem
Organizations can receive invoices that are incorrect, duplicated, unsupported by an approved purchase order, inconsistent with goods/services actually received, financially inaccurate, associated with an invalid vendor, or submitted without the required authorization.

The product must establish whether an invoice has sufficient evidence to become an approved payable obligation and must route unresolved exceptions to the correct reviewer.

## 3. Goals
1. Reduce manual invoice verification work.
2. Prevent unsupported, duplicate, or financially inconsistent invoices from becoming payable obligations.
3. Make every approval decision explainable through evidence.
4. Route exceptions to the correct role using configurable thresholds and control failures.
5. Maintain a complete audit trail from upload to payment status.
6. Provide a polished end-to-end demo suitable for a finance hackathon.

## 4. Non-Goals for MVP
- Direct banking/payment execution.
- Full ERP replacement.
- Legal/tax compliance certification.
- Autonomous fraud adjudication.
- Training a custom foundation model.
- Real-time integration with every accounting platform.

## 5. Target Users
### AP Clerk
Uploads invoices, corrects extraction fields, monitors processing.

### Procurement Manager
Resolves PO and vendor-related exceptions.

### Receiving / Operations User
Confirms goods/service receipt and resolves quantity/receipt exceptions.

### Finance Manager
Reviews financially valid invoices and approves within authority limits.

### Finance Head / CFO
Approves high-value or policy-sensitive invoices.

### Auditor
Inspects evidence, decisions, changes, and audit history.

### Admin
Configures vendors, approval thresholds, tolerances, roles, and control policies.

## 6. Personas / Primary Jobs
- AP Clerk: “Tell me what this invoice contains and what needs attention.”
- Reviewer: “Show me why this invoice is blocked and what evidence I need to resolve it.”
- Approver: “Prove that this invoice passed required controls before I authorize it.”
- Auditor: “Reconstruct exactly how this payable obligation was created.”
- Admin: “Configure policies without changing application code.”

## 7. Core Workflow
1. Invoice upload/import.
2. OCR/document extraction.
3. Normalization and validation.
4. Vendor verification.
5. PO verification.
6. Goods/service receipt verification.
7. Financial validation.
8. Duplicate and similarity detection.
9. Risk/control evaluation.
10. Exception creation and routing if required.
11. Approval workflow.
12. Payable ledger creation only after final approval.
13. Payment status tracking.
14. Audit trail at every state transition.

## 8. Product Decision Model
The system should use three layers:

**Deterministic controls**  
Arithmetic, PO matching, quantity/price/tax checks, thresholds, role permissions.

**AI-assisted controls**  
OCR, field extraction, semantic similarity, anomaly signals, natural-language explanations.

**Human controls**  
Exception resolution, high-risk review, and final authorization.

AI should not directly authorize a payment.

## 9. Functional Features
### 9.1 Invoice Intake
- Upload PDF/JPG/PNG.
- Import structured invoice data through API.
- Capture source, uploader, timestamp, checksum.
- OCR and field extraction.
- Extraction confidence per field.
- Manual correction with before/after audit entries.

### 9.2 Purchase Verification
- Match invoice to PO by PO number, vendor, or fuzzy candidate search.
- Compare PO header and line items.
- Verify PO is approved/active according to policy.
- Support partial invoicing.

### 9.3 Receipt Verification
- Match against goods receipt or service receipt.
- Support partial receipt.
- Configurable quantity/value tolerance.
- Distinguish “not received” from “receipt missing from system.”

### 9.4 Financial Validation
- Recalculate line totals.
- Recalculate subtotal, tax, and grand total.
- Validate quantity × price.
- Compare invoice price to PO price.
- Check currency and payment terms.
- Support configurable tax components.
- Record exact variance amount and percentage.

### 9.5 Duplicate Detection
- Exact duplicate by document checksum.
- Exact business-key duplicate: vendor + invoice number.
- Composite duplicate signal using vendor, PO, amount, date, line items.
- Semantic similarity using embeddings.
- Explain matching evidence.

### 9.6 Vendor Verification
- Active/inactive vendor state.
- Tax identifier field.
- Bank account and payment destination verification.
- Vendor name normalization.
- Optional change-freeze flag for payment details.

### 9.7 Approval Workflow
- Configurable amount thresholds.
- Rule-based approver selection.
- Exception-dependent routing.
- Sequential and parallel approvals.
- Approve, reject, request correction, reassign.
- Delegation support for MVP only if time permits.

### 9.8 Payable Ledger
- Create obligation only after final approval.
- Track amount, currency, due date, status.
- Statuses: APPROVED, SCHEDULED, PAID, CANCELLED, ON_HOLD.
- Aging and due-soon views.

### 9.9 Audit Trail
Capture:
- actor
- role
- action
- timestamp
- entity
- old state
- new state
- reason/comment
- evidence snapshot reference

### 9.10 Explainability
Every decision must expose:
- decision
- control checks
- failed checks
- values compared
- policy applied
- next action
- reviewer role

## 10. Success Metrics for Hackathon MVP
- ≥95% structured-field extraction on the demo invoice set.
- 100% deterministic calculation tests passing.
- 100% of blocked invoices show actionable reasons.
- 100% of invoice state transitions produce an audit record.
- Duplicate demo cases produce an explainable match signal.
- End-to-end demo invoice processing visible within seconds for preloaded/mock data.

## 11. Critical User Stories
1. As an AP Clerk, I upload an invoice and receive extracted fields with confidence indicators.
2. As the system, I match the invoice with a valid PO and receipt.
3. As a reviewer, I see why an invoice is blocked and what evidence is missing.
4. As an approver, I can approve only invoices assigned to my role and authority range.
5. As an auditor, I can replay the complete verification history.
6. As a finance user, I can see only approved obligations in the payable ledger.

## 12. Acceptance Criteria
- A valid 3-way matched invoice can progress to approval.
- A quantity mismatch cannot silently enter the payable ledger.
- A missing PO creates an exception.
- A duplicate signal creates a review path rather than silently rejecting unless policy explicitly says so.
- A vendor bank-detail mismatch blocks payment progression.
- An approver cannot approve outside their authority.
- Every manual decision records who, when, what, and why.

## 13. Recommended Demo Scenario
Use one clean invoice and one intentionally problematic invoice.

**Clean:** PO 100 units, receipt 100, invoice 100, exact price, valid vendor → approval → payable ledger.

**Exception:** PO 100 units, receipt 80, invoice 100, plus a near-duplicate submission → control graph shows mismatches, exception routes to Procurement, and invoice is prevented from entering the payable ledger until resolved.
