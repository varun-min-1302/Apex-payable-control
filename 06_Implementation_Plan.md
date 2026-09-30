# End-to-End Accounts Payable Control System — Implementation Plan

**Version:** 1.0
**Goal:** Produce a reliable, visually polished end-to-end hackathon demo without overbuilding.

## 1. Delivery Strategy
Build in vertical slices. Do not start by building every screen independently.

Priority order:
1. Core data model.
2. Invoice intake.
3. Deterministic control engine.
4. Exception workflow.
5. Approval workflow.
6. Payable ledger.
7. Audit trail.
8. AI extraction and semantic duplicate signals.
9. Analytics/polish.

## 2. Phase 0 — Repository & Foundations
### Tasks
- initialize monorepo or clearly separated frontend/backend/workers.
- configure linting, formatting, type checking.
- add env configuration.
- define database migrations.
- add CI for build/test.
- seed demo organization and users.

### Exit Criteria
Project runs locally with one command or clearly documented commands.

## 3. Phase 1 — Database & Auth
### Tasks
- create organization, user, role tables.
- vendors, POs, PO items, receipts, invoices, invoice items.
- exceptions, controls, approvals, payables, audit logs.
- authentication.
- RBAC.
- organization-level isolation.

### Tests
- user can access own organization.
- user cannot access another organization.
- AP Clerk cannot approve.

## 4. Phase 2 — Invoice Intake
### Tasks
- upload component.
- storage integration.
- checksum generation.
- invoice record creation.
- extraction job.
- structured extraction schema.
- manual correction UI.

### Demo checkpoint
Upload invoice → extracted fields appear.

## 5. Phase 3 — Deterministic Control Engine
Implement first:
```text
vendor_exists
vendor_active
po_exists
po_approved
po_vendor_match
receipt_available
quantity_within_tolerance
price_within_tolerance
arithmetic_valid
total_valid
currency_valid
bank_details_match
```

### Output
Every control returns:
```json
{
  "status": "PASS|WARN|FAIL",
  "severity": "INFO|LOW|MEDIUM|HIGH|CRITICAL",
  "expected": "...",
  "actual": "...",
  "variance": 0,
  "reason": "..."
}
```

## 6. Phase 4 — Three-Way Match UI
### Tasks
- build PO/receipt/invoice comparison table.
- line-level match visualization.
- quantity/value tolerance banners.
- evidence drill-down.

### Demo checkpoint
Show a clean invoice and an 80/100 quantity exception.

## 7. Phase 5 — Exception Engine
### Tasks
- create exceptions from failed controls.
- assign owner role.
- exception inbox.
- detail page.
- resolve/reopen.
- comments.
- state transition checks.

### Demo checkpoint
Failed invoice goes automatically to Procurement/Receiving queue.

## 8. Phase 6 — Approval Workflow
### Tasks
- approval policies.
- amount thresholds.
- route by role.
- sequential approval state.
- approve/reject/request correction.
- authority validation.

### Demo checkpoint
Two invoices with different amounts route to different approvers.

## 9. Phase 7 — Payable Ledger
### Tasks
- create payable only after approval.
- due-date calculation/storage.
- payment statuses.
- aging view.

### Demo checkpoint
Rejected/exception invoice absent from payable ledger; approved invoice appears.

## 10. Phase 8 — Duplicate & Semantic Similarity
### Tasks
1. checksum duplicate.
2. vendor + invoice number duplicate.
3. composite similarity.
4. embedding similarity.
5. candidate comparison UI.

### Demo checkpoint
Upload two visually/semantically similar invoices with slightly changed formatting; show similarity evidence.

## 11. Phase 9 — AI Explainability
AI should generate explanations only from structured evidence.

Prompt pattern:
```text
Given these control results and source values, explain why the invoice is or is not ready for payable approval.
Do not invent facts.
Use only supplied evidence.
Return concise structured output.
```

Add:
- “Why not payable?”
- “What changed?”
- reviewer handoff summary.

## 12. Phase 10 — Audit & Observability
### Tasks
- audit events on state changes.
- audit explorer.
- correlation IDs.
- structured logs.
- worker job status.

## 13. Phase 11 — Dashboard & Visual Polish
Add:
- KPI cards.
- control health.
- exception trends.
- payable due-soon summary.
- recent activity.

Polish:
- loading states.
- empty states.
- responsive tables.
- keyboard support.
- error states.

## 14. Phase 12 — Testing
### Unit Tests
- financial calculations.
- tolerance rules.
- duplicate fingerprint.
- state transitions.
- approval thresholds.

### Integration Tests
- invoice → controls → exception.
- invoice → approvals → payable.
- retry does not duplicate payable.
- bank mismatch blocks progression.

### Security Tests
- cross-tenant access.
- privilege escalation.
- direct API approval attempt.
- invalid upload.

## 15. Phase 13 — Demo Hardening
Create a fixed demo dataset.

Demo users:
- ap@demo
- procurement@demo
- finance@demo
- auditor@demo

Demo data:
- 3 vendors
- 3 POs
- 3 receipts
- 4 invoices
- 1 clean invoice
- 1 quantity mismatch
- 1 price mismatch
- 1 duplicate pair

## 16. Suggested Team Split
### Member 1 — Backend / Database
Auth, schema, API, workflow, controls.

### Member 2 — Frontend
Dashboard, invoice details, match view, exception center.

### Member 3 — AI / Document Processing
OCR, extraction, embeddings, similarity, explanation layer.

### Member 4 — Security / Testing / Integration
RBAC, audit, threat controls, integration testing, deployment.

## 17. Definition of Done
A feature is complete only when:
- backend logic exists,
- UI is wired to real backend state,
- authorization is checked server-side,
- errors are handled,
- audit entry exists where required,
- automated tests cover critical paths.

## 18. MVP Cut Line If Time Is Tight
Keep:
- upload
- extraction
- PO/receipt/invoice 3-way match
- financial validation
- duplicate detection
- exception routing
- approval threshold
- payable ledger
- audit timeline

Defer:
- advanced analytics
- external ERP integrations
- payment execution
- complex delegation
- advanced anomaly models
