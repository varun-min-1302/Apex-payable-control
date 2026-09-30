# End-to-End Accounts Payable Control System — Frontend Design & UX Specification

**Version:** 1.0

## 1. UX Goal
Create a premium, trustworthy finance-control interface. The visual language should feel like modern enterprise software: restrained, clear hierarchy, dense data where needed, strong evidence presentation, and zero “AI magic” that hides why a decision was made.

## 2. Navigation
Primary left navigation:
- Overview
- Invoices
- Exceptions
- Approvals
- Payable Ledger
- Vendors
- Purchase Orders
- Receipts
- Audit Trail
- Settings

Top bar:
- global search
- notifications
- current workspace/company
- user menu

## 3. Routes
```text
/dashboard
/invoices
/invoices/new
/invoices/:id
/invoices/:id/matching
/exceptions
/exceptions/:id
/approvals
/payables
/vendors
/vendors/:id
/purchase-orders
/receipts
/audit
/settings
```

## 4. Screen Specifications
### 4.1 Dashboard
Hero KPI cards:
- invoices received
- awaiting validation
- exceptions
- approvals pending
- payable value
- due within 7 days

Main sections:
- control health matrix
- exception queue
- approval queue
- payable aging
- recent audit events

### 4.2 Invoice Intake
Two-column layout:
Left: upload dropzone + document preview.  
Right: extracted fields + confidence.

State progression:
```text
Uploaded → Extracting → Validating → Decision Ready
```

Confidence indicators should never equal approval status.

### 4.3 Invoice Details
Header:
- invoice number
- vendor
- amount
- status
- due date
- risk/control status

Tabs:
- Overview
- Items
- 3-Way Match
- Controls
- Exceptions
- Approvals
- Audit

### 4.4 Control Center / Evidence Panel
Display each control as a card:
```text
✓ Vendor verified
✓ PO matched
✓ Receipt matched
⚠ Price variance
✓ Tax calculation
🔴 Bank details mismatch
```

Clicking a control opens:
- policy used
- expected value
- actual value
- variance
- source document/record
- next action

### 4.5 Three-Way Match View
A visual comparison table:
```text
Field          PO        Receipt       Invoice      Result
------------------------------------------------------------
Item           Laptop    Laptop        Laptop       ✓
Quantity       100       80            100          🔴
Unit Price     50,000    —             52,000       🔴
PO Status      Approved  —             —            ✓
```

### 4.6 Exception Center
Prioritize by severity and age.

Filters:
- severity
- exception type
- assigned role
- assigned user
- age
- amount

Each card shows:
- invoice
- vendor
- amount
- reason
- current owner
- SLA/age
- next action

### 4.7 Exception Detail
Use “Why not payable?” as the top action.

Sections:
1. Decision summary.
2. Failed controls.
3. Evidence comparison.
4. Recommended next action.
5. Assignment.
6. Resolution notes.
7. Audit history.

### 4.8 Approval Center
Queue by authority.

Approval page must show:
- invoice preview
- matched PO/receipt evidence
- control summary
- exceptions/resolutions
- audit timeline
- approve/reject/request correction

Avoid a single oversized “Approve” button without evidence.

### 4.9 Payable Ledger
Table fields:
- invoice
- vendor
- approved amount
- due date
- status
- age
- payment reference

Summary:
- total outstanding
- due soon
- overdue
- paid this period

### 4.10 Audit Explorer
Two-pane layout:
left entity/event filters; right event timeline.

Timeline event sample:
```text
10:41 Invoice uploaded
10:42 OCR completed
10:42 PO matched
10:43 Quantity variance detected
10:45 Exception assigned to Procurement
11:02 Exception resolved
11:10 Finance approved
```

### 4.11 Vendor Detail
Show:
- identity
- active status
- open invoices
- PO history
- receipt/exception history
- payment-detail change history

Sensitive bank fields must be masked.

## 5. Design System
### Color semantics
Use semantic status tokens, not decorative colors:
- success
- warning
- danger
- neutral
- informational

Avoid neon/cyberpunk styling.

### Typography
- Strong page titles.
- Medium-weight section labels.
- Tabular numerals for amounts.
- Monospace only for IDs/hash/correlation IDs where useful.

### Components
- App shell
- KPI card
- Data table
- Status chip
- Evidence card
- Match matrix
- Timeline
- Upload zone
- Document viewer
- Drawer/modal
- Approval action bar
- Exception card
- Empty state
- Skeleton loader
- Toast/alert

## 6. Responsive Behavior
Desktop-first because finance workflows are data-heavy, but responsive down to tablet.

At narrower widths:
- collapse sidebar
- convert dense tables to stacked records
- keep decision/evidence header sticky
- maintain access to primary actions

## 7. Accessibility
- WCAG-oriented contrast.
- Full keyboard navigation.
- Focus states.
- Screen-reader labels on icon-only buttons.
- Never use color as the only status indicator.
- Confirm destructive actions.

## 8. Frontend State Model
Server state:
- invoice
- controls
- exceptions
- approvals
- payables
- vendors

Client state:
- filters
- selected tab
- upload progress
- modal state
- temporary form edits

Do not keep authoritative invoice workflow state only in browser memory.

## 9. Frontend Data Fetching
Recommended pattern:
- query cache for server state
- optimistic UI only for low-risk non-authoritative actions
- invalidate relevant queries after workflow mutation
- polling/SSE for long-running extraction jobs

## 10. UX Rules
1. Always show “what happened” and “why.”
2. Never imply AI confidence equals accounting validity.
3. Keep evidence one click away.
4. Show exact amounts and variances.
5. Prevent accidental approval.
6. Preserve user context after actions.
