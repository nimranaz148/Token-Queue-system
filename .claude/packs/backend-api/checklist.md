# Backend API (framework-agnostic) — checklist

Every item must be answered in the PRD before Phase 1 exits. Each becomes a requirement and a candidate acceptance test.

- [ ] C-BA-01 Every endpoint validates input and rejects unknown or oversized fields with a consistent error format.
- [ ] C-BA-02 Authorisation is tested per endpoint and per role, including the case of a valid user reading another user's or tenant's data.
- [ ] C-BA-03 List endpoints are paginated with a hard maximum page size and a stable sort.
- [ ] C-BA-04 Requests that may be retried (payments, orders, imports) are idempotent or carry an idempotency key.
- [ ] C-BA-05 Migrations apply to an empty database and to a copy of production data, and each has a tested way back or a stated reason it has none.
- [ ] C-BA-06 Filtered and joined columns are indexed; the slowest queries are measured with realistic data volume.
- [ ] C-BA-07 Transaction boundaries are explicit; a failure half-way leaves no partial records.
- [ ] C-BA-08 Every outbound call has a timeout and a defined failure behaviour.
- [ ] C-BA-09 Health and readiness endpoints exist and reflect real dependencies.
- [ ] C-BA-10 Logs are structured, carry a request id, and never contain secrets or personal data.
- [ ] C-BA-11 CORS is an allowlist; secrets come from the environment or a secret manager, never the repository.
- [ ] C-BA-12 The OpenAPI document matches the running service; the generated client is checked for drift.
- [ ] C-BA-13 Rate limits protect authentication and expensive endpoints.
- [ ] C-BA-14 Personal data is identified, minimised, and has a stated retention and deletion rule.
- [ ] C-BA-15 A restore from backup has been performed once and timed.
