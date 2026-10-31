# DevOps and infrastructure — checklist

Every item must be answered in the PRD before Phase 1 exits. Each becomes a requirement and a candidate acceptance test.

- [ ] C-DI-01 Every verify lane has a CI workflow that calls the same script developers run locally.
- [ ] C-DI-02 The main branch is protected: required checks, no force-push, review required.
- [ ] C-DI-03 A preview or staging environment exists and matches production configuration except for scale and data.
- [ ] C-DI-04 No secret is in the repository or its history; a secret scan runs on every push.
- [ ] C-DI-05 Dependency and container-image vulnerability scans run on a schedule and on change.
- [ ] C-DI-06 Infrastructure is either defined as code or documented step by step so a stranger can rebuild it.
- [ ] C-DI-07 Backups run automatically and a restore has been performed and timed.
- [ ] C-DI-08 A rollback has been practised and takes less than the PRD recovery target.
- [ ] C-DI-09 Uptime and error-rate monitoring alert a named person; alerts have runbooks.
- [ ] C-DI-10 Logs are retained for a stated period and contain no secrets or personal data.
- [ ] C-DI-11 TLS is enforced with HSTS; certificates renew automatically.
- [ ] C-DI-12 Access follows least privilege; every human and service account has a documented purpose.
- [ ] C-DI-13 A budget alert exists for cloud spend.
- [ ] C-DI-14 Recovery point and recovery time objectives are documented and match the PRD.
