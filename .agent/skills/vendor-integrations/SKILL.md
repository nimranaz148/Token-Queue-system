---
name: vendor-integrations
description: Reference and execution guide for external vendor integrations (Supabase Auth & Realtime, Cloudflare Turnstile, Sentry) with strict contract adherence, sandbox verification, and credential protection.
---

# Vendor Integrations Skill

This skill provides verified operational procedures, contract constraints, and sandbox testing protocols for all third-party vendor services integrated into the Clinic Token & Queue SaaS.

---

## 1. Supabase Auth & JWT Verification

- **Vendor Documentation URL:** https://supabase.com/docs/guides/auth
- **Documentation Retrieval Date:** 2026-10-31
- **Service Role:** Staff magic-link authentication, session token issuing, and public JWKS endpoint validation.

### Implementation Protocol:
- Browser requests magic link via FastAPI (`POST /api/v1/auth/magic-link`).
- The API dispatches magic link delivery via Supabase GoTrue Auth API or custom SMTP.
- Incoming bearer tokens are verified locally against Supabase's JWKS public keys.
- **Caching Contract:** JWKS keys are cached in-memory with a 10-minute TTL to prevent rate limits and network latency.
- **Tenant Scope:** The user's membership table (`staff_members`) maps `user_id` to `clinic_id` and assigned roles.

---

## 2. Cloudflare Turnstile

- **Vendor Documentation URL:** https://developers.cloudflare.com/turnstile/get-started/server-side-validation/
- **Documentation Retrieval Date:** 2026-10-31
- **Service Role:** Bot detection and anti-abuse verification on public token booking endpoints (`POST /api/v1/tokens/book`).

### Implementation Protocol:
- Frontend renders Cloudflare Turnstile widget on patient booking screen (F-001).
- Frontend sends `turnstile_token` in booking request payload.
- Backend verifies via `POST https://challenges.cloudflare.com/turnstile/v0/siteverify` using `httpx.AsyncClient` with a strict 3-second timeout.
- **Sandbox Test Keys:**
  - `1x0000000000000000000000000000000AA`: Always passes verification (development/sandbox).
  - `2x0000000000000000000000000000000AA`: Always fails verification (for testing rejection).
- **Graceful Degradation:** If Cloudflare times out, fail-open or log security warning according to clinic security mode while recording an audit event.

---

## 3. Sentry Error & Performance Monitoring

- **Vendor Documentation URL:** https://docs.sentry.io/platforms/python/guides/fastapi/
- **Documentation Retrieval Date:** 2026-10-31
- **Service Role:** Production exception tracking, distributed tracing, and slow query monitoring.

### Implementation Protocol:
- Initialized in `apps/api/app/integrations/sentry.py` via `sentry_sdk.init`.
- **Non-Negotiable PII Scrubbing:** All patient identifiers (`patient_name`, `phone`, `email`, raw notes) MUST be redacted or masked before transmission.
- **Non-blocking Buffer:** Transmission errors or timeout events must buffer in-memory or drop silently without blocking incoming HTTP requests.
- **Duplicate Suppression:** Duplicate errors within a 5-second window are coalesced to avoid alerting floods.

---

## 4. Supabase Realtime Broadcast

- **Vendor Documentation URL:** https://supabase.com/docs/guides/realtime
- **Documentation Retrieval Date:** 2026-10-31
- **Service Role:** Real-time queue state broadcasts to waiting room TV displays and patient status views.

### Implementation Protocol:
- Channels are scoped per clinic and doctor: `clinic:{clinic_id}:doctor:{doctor_id}:queue`.
- **Non-Negotiable Realtime Payload Constraint:**
  - Realtime payloads contain ONLY token numbers (e.g. `A-014`), doctor ID, current token status (`CALLED`, `SERVING`), and wait counts.
  - NEVER broadcast patient names, phone numbers, or clinical notes over Realtime channels.

---

## 5. Verification Checklist

1. **Zero Secrets in Repo:** Run `pytest tests/unit/test_vendor_sandbox.py` to confirm zero credentials in git.
2. **Sandbox Call Verification:** Ensure sandbox ping succeeds using vendor dummy credentials.
3. **Contract Adherence:** Ensure all payloads conform to OpenAPI specifications and vendor rate limits.
