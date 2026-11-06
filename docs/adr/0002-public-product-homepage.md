# ADR 0002 — Public Product Homepage

- **Status:** accepted
- **Date:** 2026-11-06
- **Change request:** CR-001
- **Approver:** Product owner (explicit request in this session)

## Context

The root route (`/`) currently shows a generic title, one sentence, and a staff login button. It does not explain the clinic queue product to clinic owners and staff arriving at the site.

## Decision

Redesign the existing root route as a public product overview for the Clinic Token & Queue SaaS. Keep the staff login link pointed at `/login`. Keep patient booking at each clinic's existing `/c/{slug}` link; the homepage will not invent a clinic selector or booking flow.

The page may explain the product's documented capabilities: online token booking, one queue for online and walk-in patients, doctor NEXT controls, live patient/TV updates, and owner reports. It will use a labeled sample interface preview, without presenting sample values as live clinic data. It adds no API, stored data, business rule, or account flow.

## Change request assessment

| Field | Assessment |
| --- | --- |
| Scope | Public marketing/product overview on the existing `/` route, responsive for phones and desktop |
| Business reason | Explain the product before asking clinic staff to sign in |
| Effort | About one developer day |
| Schedule impact | One day for this change; no phase scope changes |
| Cost impact | No new service, API, or recurring cost |
| Affected PRD sections | §27 product structure, §29 public homepage wireframe, §25 change log |
| Decision | Approved |

## Consequences

- The root page becomes useful to clinic owners and staff while the existing role-protected application routes remain unchanged.
- The visual language follows the approved warm paper and botanical teal design tokens.
- The homepage makes no claims about actual clinic adoption, time savings, uptime, or performance metrics.
