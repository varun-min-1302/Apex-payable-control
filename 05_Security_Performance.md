# End-to-End Accounts Payable Control System — Security & Performance Specification

**Version:** 1.0

## 1. Security Objectives
1. Prevent unauthorized access to invoices and financial records.
2. Prevent cross-organization data access.
3. Prevent unauthorized approvals.
4. Protect invoice documents and payment information.
5. Make audit records difficult to tamper with.
6. Minimize sensitive data exposure to AI providers.

## 2. Threat Model
### Threat: Broken access control
**Risk:** User accesses another organization's invoice.  
**Mitigation:** organization_id scoping, database row-level policies, service authorization, tests for IDOR.

### Threat: Privilege escalation
**Risk:** AP Clerk calls approval endpoint directly.  
**Mitigation:** role + assigned workflow step + authority check in backend.

### Threat: Duplicate payment
**Risk:** Same invoice is submitted twice.  
**Mitigation:** checksum, business-key uniqueness, composite matching, semantic similarity, mandatory review policy.

### Threat: Vendor bank change
**Risk:** Invoice redirects payment to unregistered account.  
**Mitigation:** strict bank-detail comparison, masking, mandatory hold, dual review for change.

### Threat: Malicious file upload
**Risk:** malformed or malicious document.  
**Mitigation:** file type allowlist, size limits, malware scanning if available, isolated processing, never execute uploaded content.

### Threat: Prompt injection in invoice text
**Risk:** Invoice text attempts to instruct the AI.  
**Mitigation:** treat extracted text as untrusted data, separate system instructions from document content, use schema-constrained extraction, deterministic controls for decisions.

### Threat: AI hallucination
**Risk:** model invents accounting evidence.  
**Mitigation:** LLM can only produce structured extraction/explanation based on provided evidence; final values come from database/rule engine.

### Threat: Audit tampering
**Risk:** ordinary users edit audit history.  
**Mitigation:** append-only model, DB permissions, immutable/exported log sink in production.

### Threat: Credential theft
**Mitigation:** short-lived tokens, secure cookies where applicable, MFA for privileged roles in production, secrets manager, no secrets in source control.

### Threat: Data leakage to AI provider
**Mitigation:** redact unnecessary PII/bank data, send only minimum document content, configurable provider adapter, record provider request metadata without raw sensitive payload when possible.

## 3. Authentication
- OIDC/JWT or managed auth provider.
- Short session expiry for privileged actions.
- Re-authentication/step-up authentication for sensitive admin/payment actions where available.

## 4. Authorization Matrix
| Action | AP | Procurement | Receiving | Finance | Auditor | Admin |
|---|---:|---:|---:|---:|---:|---:|
| Upload invoice | ✓ | optional | — | ✓ | — | ✓ |
| Edit extraction | ✓ | optional | — | ✓ | — | ✓ |
| Resolve PO exception | — | ✓ | — | optional | — | ✓ |
| Resolve receipt exception | — | — | ✓ | optional | — | ✓ |
| Approve payable | — | optional | — | ✓ | — | ✓ |
| View audit | own/assigned | own/assigned | own/assigned | org | org read-only | org |
| Configure policy | — | — | — | — | — | ✓ |

Backend must enforce this table; frontend visibility is not a security control.

## 5. Sensitive Data Handling
- Mask bank account details in UI.
- Encrypt in transit using HTTPS/TLS.
- Use encryption at rest from the managed database/object store.
- Avoid logging full bank accounts, tax IDs, access tokens, or raw documents.
- Use secure document URLs with short expiry.

## 6. Secure File Processing
- Max size limit.
- Extension + MIME validation.
- Store outside executable paths.
- Generate random storage keys.
- Run OCR in worker process.
- Sanitize extracted text.
- Reject unsupported formats.

## 7. API Security
- Schema validation on every endpoint.
- Rate limit authentication and upload endpoints.
- Idempotency keys for mutations that can be retried.
- CSRF protection where cookie auth is used.
- CORS allowlist.
- Security headers.
- Structured error handling.

## 8. Audit Security
For each audit event:
```text
actor_id
organization_id
action
entity
old_state
new_state
reason
request_id
created_at
```
Optionally compute a chained digest:
```text
hash_n = SHA256(hash_(n-1) + canonical(event_n))
```
This does not replace a proper immutable log store, but improves tamper evidence for the hackathon.

# Performance

## 9. Performance Targets
Interactive reads/writes:
- p50 < 200 ms
- p95 < 500 ms
- p99 < 1 s

Document-processing jobs:
- return job ID immediately.
- first visible status within 1–2 seconds after enqueue.
- complete typical demo invoice in <15 seconds on a warm system; actual OCR/LLM latency may vary by provider.

## 10. Performance Strategy
### Database
- Index `organization_id` + common filters.
- Index invoice number, vendor ID, PO ID, status, due date.
- Composite indexes for duplicate keys.
- Avoid N+1 queries for invoice detail pages.

### API
- Pagination on all list endpoints.
- Stable sorting.
- Field selection for large tables if needed.
- Cache mostly static configuration.

### Worker
- Separate extraction from control evaluation.
- Parallelize independent control checks.
- Cap concurrency based on provider/database limits.
- Retry transient failures with backoff.

### Semantic Search
- Precompute embeddings.
- Index vectors with pgvector.
- Search top-k candidates, then run exact/composite checks.

## 11. Caching
Good candidates:
- role/permission configuration
- policy configuration
- vendor normalization dictionary
- dashboard aggregates for short periods

Do not cache mutable authorization decisions without strict invalidation.

## 12. Reliability
- Job retry with exponential backoff.
- Dead-letter queue for repeated worker failure.
- Idempotent processing.
- Database transactions around state changes + audit creation.
- Prevent partial workflow updates.

## 13. Performance Test Cases
- 10 concurrent invoice uploads.
- 1000 invoice list records with filters.
- 10k historical invoices for duplicate search.
- Large exception queue pagination.
- Repeated webhook/job delivery.
- Burst of approval actions.

## 14. Success Criteria
No cross-tenant result from any query.  
No unauthorized approval accepted by API.  
No duplicate payable created by retry.  
Core read/write p95 remains below target under hackathon-scale load.
