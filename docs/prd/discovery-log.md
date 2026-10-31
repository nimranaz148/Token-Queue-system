# Discovery Log — Clinic Token & Queue SaaS

| Round | Question | Answer | Date |
| --- | --- | --- | --- |
| 0 | Existing spec? | None. Source = 16 blueprint screenshots in `context-images/` (summarised in `APP_OVERVIEW.md`) | 2026-10-31 |
| 0 | What is it? | Clinic app: online token, live queue, reception list, doctor panel, TV screen, owner report — 5 roles, 12 screens | 2026-10-31 |
| 1 | Profile | Production | 2026-10-31 |
| 1 | Budget | Free tiers only | 2026-10-31 |
| 1 | Team / timeline | 1 developer, ~10-12 weeks | 2026-10-31 |
| 2 | Tenancy | Multiple clinics (SaaS), data isolated per clinic | 2026-10-31 |
| 2 | Language | English + Roman Urdu UI, i18n-ready | 2026-10-31 |
| 3 | Phases | 5 (Phase 0 foundation + 4) | 2026-10-31 |
| 3 | Clinic billing | Not now; add after the first 1-2 clinics are live | 2026-10-31 |
| 4 | Stack | Next.js + FastAPI + Supabase (Postgres, Auth) | 2026-10-31 |
| 6 | AI features? | Yes | 2026-10-31 |
| 6 | AI jobs | Patient chat assistant, owner daily brief, visit-notes summary, wait-time prediction | 2026-10-31 |
| 6 | AI provider | OpenRouter primary, Google Gemini fallback | 2026-10-31 |
| U1 | Country (Q-001) | Pakistan | 2026-10-31 |
| U1 | Staff login (Q-002) | Email magic link | 2026-10-31 |
| U1 | Visit notes to patient | Clinic decides with an on/off setting ("it depends on them") | 2026-10-31 |
| U2 | Dev email delivery (Q-007) | Hosted Supabase project uses custom SMTP with a Gmail app password (dev only); confirmation email delivered and link signed in on 2026-10-20 | 2026-10-31 |
| U2 | Why custom SMTP | Built-in Supabase sender allows ~2 emails/hour per project, not usable | 2026-10-31 |
| U3 | Email sender (Q-007) | Owner decision: keep Gmail SMTP app password; own-domain sender deferred | 2026-10-31 |
