# Vertical Slice Architecture Pattern (Web-App & Backend Packs)

This document defines the standard 6-layer vertical slice pattern for features in the Clinic Token & Queue SaaS codebase. Every feature built across the monorepo adheres strictly to this structure.

---

## The 6-Layer Anatomy

```
┌────────────────────────────────────────────────────────┐
│ 1. Database Model (SQLAlchemy + Alembic)                │
│    - clinic_id tenant scoping, UUID PKs, SoftDelete     │
├────────────────────────────────────────────────────────┤
│ 2. Domain Service (apps/api/app/services/)             │
│    - Business rules, atomic row locks, AuditService    │
├────────────────────────────────────────────────────────┤
│ 3. REST Router (apps/api/app/routers/)                 │
│    - Explicit permission guard, Rule 8 & 9 compliance  │
├────────────────────────────────────────────────────────┤
│ 4. Typed Contract (OpenAPI & Schemas)                  │
│    - Pydantic v2 schemas, generated client types       │
├────────────────────────────────────────────────────────┤
│ 5. Next.js App Router UI (apps/web/src/app/)           │
│    - 4 states (loading, empty, error, unauthorized)    │
│    - Design tokens, double-submit protection           │
├────────────────────────────────────────────────────────┤
│ 6. Automated Verification (Fast-tier CI)               │
│    - Pytest unit/audit tests + Vitest component tests  │
└────────────────────────────────────────────────────────┘
```

---

## Layer Guidelines

### 1. Database Model (`apps/api/app/models/`)
- Every tenant table includes `clinic_id: Mapped[uuid.UUID]` with foreign key to `clinics.id`.
- Inherits `BaseModel`, `TimestampMixin` (`created_at`, `updated_at` with UTC).
- Soft delete via `SoftDeleteMixin` (`deleted_at: Mapped[datetime | None]`).
- Every schema modification ships with an Alembic migration in the same commit.

### 2. Domain Service (`apps/api/app/services/`)
- Pure business logic resides here. Routers and AI agents NEVER run database queries or mutations directly.
- Multi-tenant filter applied to every query: `where(Model.clinic_id == clinic_id, Model.deleted_at.is_(None))`.
- Concurrency locks: Sequential counters use atomic row locks (`SELECT ... FOR UPDATE`).
- Auditing: Every state mutation records an immutable audit log entry via `AuditService.record_audit`.

### 3. REST Router (`apps/api/app/routers/`)
- Routers declare routes under `/api/v1/<resource>`.
- **Rule 8:** Routers never import `app.models.*` directly.
- **Rule 9:** Every endpoint declares an explicit permission dependency (`require_roles`, `require_clinic_member`, or `allow_public`).
- Scoped strictly to `current_user.clinic_id`. Cross-tenant queries return 404 Not Found.

### 4. Typed Contract & Schemas (`apps/api/app/schemas/`)
- Strictly validated using Pydantic v2.
- Input models validate field lengths, formats (e.g. E.164 phone numbers), and constraints.
- Response models use `model_config = ConfigDict(from_attributes=True)`.

### 5. Frontend UI Page (`apps/web/src/app/`)
- Uses React Server Components (RSC) by default; `"use client"` only when interactive state, effects, or browser APIs are needed.
- Enforces the 4 mandatory states:
  1. **Loading:** Skeleton rows or cards (never bare spinners).
  2. **Empty:** Dedicated empty screen with contextual call-to-action button.
  3. **Error:** Human-readable error banner with retry trigger.
  4. **Unauthorized:** Clear access denied message when role check fails.
- Forms include double-submit protection (disabling button during submission) and field-level validation feedback.

### 6. Automated Verification
- Fast-tier execution:
  - Python: `ruff check`, `mypy --strict`, `pytest`.
  - Web: `tsc --noEmit`, `vitest run`.
  - Architecture contracts: `test_ai_isolation.py`, `test_api_conventions.py`.
