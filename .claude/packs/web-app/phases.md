# Web application — phases

Phase 0 and Phase 1 are a production MVP: the smallest thing real users can rely on. Anything bigger is deferred with its trigger.

## Phase 0

- Scaffold the web app with the chosen framework, strict TypeScript, lint and format — Accept: Fresh clone installs and builds; lint and typecheck run in the fast tier
- Design tokens and layout shell — Accept: Tokens are the only source of colour, type and spacing; shell renders at 360 px and 1440 px without horizontal scroll
- Authentication and role guard — Accept: Login, logout and expiry work; a user without the role gets 403 on a protected route
- Deploy a preview environment on a free tier — Accept: Every pull request gets a preview URL; production deploy is one command

## Phase 1

- First vertical slice through the UI, API and database — Accept: The slice works end to end with one automated test; the pattern is written down
- Form pattern: validation, error display, double-submit protection — Accept: Server and client reject the same invalid inputs; a second click does not create a second record
- Accessibility and performance gates — Accept: axe finds no serious issue on the slice; the performance budget lane passes
- End-to-end smoke test of the critical flow — Accept: One browser test signs in and completes the main task

## Deferred

- CDN and caching tuning — Trigger: p95 time to first byte is above the PRD target for a week
- Internationalisation — Trigger: A second language or market is committed
- Feature flags and A/B testing — Trigger: Two or more releases are blocked by the same unfinished feature, or a decision needs measured data
- Offline or installable app (PWA) — Trigger: Users must work without connectivity, as stated in the PRD
