# AP Control System — Backend Quick Reference

## Core Tables

```text
TENANTS
USERS
VENDORS
VENDOR_BANK_ACCOUNTS
PURCHASE_ORDERS
PURCHASE_ORDER_ITEMS
GOODS_RECEIPTS
GOODS_RECEIPT_ITEMS
DOCUMENTS
INVOICES
INVOICE_ITEMS
INVOICE_REVISIONS
CONTROL_RUNS
CONTROL_RESULTS
RISK_SIGNALS
INVOICE_FINGERPRINTS
EXCEPTIONS
APPROVAL_POLICIES
APPROVAL_REQUESTS
PAYABLE_LEDGER
AUDIT_EVENTS
IDEMPOTENCY_KEYS
```

## Core Relations

```text
Tenant
  ├── Users
  ├── Vendors
  │     └── Bank Accounts
  ├── Purchase Orders
  │     └── PO Items
  │           └── Goods Receipt Items
  ├── Invoices
  │     ├── Invoice Items
  │     ├── Revisions
  │     ├── Control Runs
  │     │     └── Control Results
  │     ├── Risk Signals
  │     ├── Exceptions
  │     ├── Approval Requests
  │     └── Payable Ledger
  └── Audit Events
```

## Core state machine

```text
RECEIVED
  -> PROCESSING
  -> VALIDATING
  -> EXCEPTION <-> VALIDATING
  -> AWAITING_APPROVAL
  -> APPROVED
  -> PAYABLE_CREATED
  -> PAID

Any blocking failure:
  -> EXCEPTION

Rejected:
  -> REJECTED

Approved correction:
  -> new invoice revision
  -> new control run
```

## Control categories

```text
VENDOR
PROCUREMENT
RECEIPT
FINANCIAL
DUPLICATE
APPROVAL
SECURITY
```

## Control statuses

```text
PASS
WARN
FAIL
NOT_APPLICABLE
```

## API groups

```text
/api/v1/auth
/api/v1/invoices
/api/v1/vendors
/api/v1/purchase-orders
/api/v1/receipts
/api/v1/controls
/api/v1/exceptions
/api/v1/approvals
/api/v1/payables
/api/v1/dashboard
```

## Golden transaction

```text
SELECT invoice FOR UPDATE
  -> verify permissions
  -> verify state
  -> verify controls
  -> verify approvals
  -> create payable IF NOT EXISTS
  -> set invoice status
  -> write audit event
COMMIT
```
