# Third-party integrations (Salesforce, OAuth providers, payments, marketplaces, email) — checklist

Every item must be answered in the PRD before Phase 1 exits. Each becomes a requirement and a candidate acceptance test.

- [ ] C-I-01 A sandbox or recorded-fixture suite proves the happy path for every integration without touching production.
- [ ] C-I-02 Tokens refresh automatically; revocation and re-consent are handled and tested.
- [ ] C-I-03 Requested scopes are the minimum needed and each is justified in the PRD.
- [ ] C-I-04 Incoming webhooks verify the signature, reject replays, and are idempotent.
- [ ] C-I-05 Outgoing calls use timeouts, retries with backoff and jitter, and a dead-letter or failure record after the last retry.
- [ ] C-I-06 Vendor rate limits are respected, and a 429 response is handled.
- [ ] C-I-07 Vendor error codes are mapped to our error format; raw vendor errors never reach users.
- [ ] C-I-08 The vendor is mocked in CI so builds do not depend on the vendor being up.
- [ ] C-I-09 A data-mapping table lists each field, its source, its destination and any transformation.
- [ ] C-I-10 Credentials are stored in a secret manager and have a rotation procedure.
- [ ] C-I-11 The vendor API version is pinned and a change-notice source is subscribed to.
- [ ] C-I-12 Failures are monitored and alert a human when the failure rate crosses the stated threshold.
- [ ] C-I-13 The vendor's terms and data-processing obligations are read and any personal-data transfer is recorded.
