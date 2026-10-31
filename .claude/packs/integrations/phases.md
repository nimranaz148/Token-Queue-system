# Third-party integrations (Salesforce, OAuth providers, payments, marketplaces, email) — phases

Phase 0 and Phase 1 are a production MVP: the smallest thing real users can rely on. Anything bigger is deferred with its trigger.

## Phase 0

- Vendor accounts, sandbox access and credentials in the secret manager — Accept: A sandbox call succeeds from the dev environment; no credential is in the repository
- Integration skill: install an upstream one or generate a project-local one — Accept: The skill cites the vendor documentation URL and date

## Phase 1

- Authentication to the vendor (OAuth or key) with token refresh — Accept: Expired token refreshes without user action; revoked token produces a clear re-consent path
- One end-to-end integration flow against the sandbox — Accept: Contract test passes against a recorded response; timeout, 429 and error response each have a test
- Webhook endpoint with signature verification and idempotency — Accept: A replayed event is ignored; a bad signature is rejected
- Failure handling and alerting — Accept: A forced vendor outage shows the defined degraded behaviour and raises an alert

## Deferred

- Bulk sync and backfill jobs — Trigger: Initial data volume cannot be handled by the incremental path
- Second vendor in the same category — Trigger: A customer requires it; extract a vendor-neutral interface then, not before
- Real-time sync instead of polling — Trigger: Polling latency breaks a stated user need
