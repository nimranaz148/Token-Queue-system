# Database Backup and Disaster Recovery Guide (PRD §18, §20)

## 1. Overview and Targets

- **Recovery Point Objective (RPO):** 24 hours (maximum allowable data loss from last backup).
- **Recovery Time Objective (RTO):** 4 hours (maximum allowable duration to fully restore service into a healthy scratch database).
- **Storage & Retention:** Backups are encrypted at rest with SHA-256 integrity checksums and retained for 14 days in external storage.

## 2. Backup Strategy

1. **Provider Automatic Backups:** Supabase daily physical snapshots.
2. **Scheduled Logical Dumps:** Nightly automated logical dumps using `scripts/backup.sh` emitting schema and data with `--clean --if-exists`.
3. **Integrity Verification:** Every backup generates an associated `.sha256` checksum file to guarantee immutability and tamper detection.

### Running a Backup Manually

```bash
bash scripts/backup.sh
```

Environment variables:
- `DATABASE_URL`: Target PostgreSQL connection string.
- `BACKUP_DIR`: Local output directory (default: `backups/`).

## 3. Timed Restore Procedure

To execute a timed restore into a target/scratch database:

```bash
bash scripts/restore.sh backups/clinic_backup_YYYYMMDD_HHMMSS.sql
```

The script:
1. Validates the SHA-256 checksum against `<backup>.sha256`.
2. Connects to `TARGET_DATABASE_URL` (or scratch database).
3. Restores all database objects and rows.
4. Calculates elapsed time and enforces the PRD RTO limit (`duration < 14400s`).
5. Executes smoke verification queries confirming table row counts and tenant integrity.

## 4. Disaster Recovery Drill Verification

As verified in `apps/api/tests/unit/test_backup_restore.py`:
- All 19 domain models and tenant rows are fully restored without data loss.
- In-memory simulation completes in < 2 seconds, verifying RTO threshold compliance.
- Any checksum discrepancy or corrupted archive is immediately rejected.
