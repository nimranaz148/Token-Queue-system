<!--
PRD TEMPLATE — used by the `prd` skill. It mirrors the section structure of a full SOW/SRS (sections 1-38) so every
project gets the same dense, hand-off-ready document, with technical detail included.

Rules for filling it:
- Keep the numbering. If a section does not apply, KEEP the heading and write "Not applicable — <reason>". Stable numbers
  let people say "see PRD §13" across projects and let `bootstrap` and `architect` cite sections.
- Every requirement is testable and uses "shall". No adjectives without a number ("fast" -> "p95 < 300 ms").
- Every screen/form has an ID (F-001…), every dashboard (D-001…), every report (R-001…), every workflow (W-001…),
  every integration (I-001…). IDs never get reused.
- Never invent facts. Unknowns go to §0.4 Open Questions; guesses go to §0.3 Assumptions.
- Delete these HTML comments in the final document.
-->
---
project: "{{Project name}}"
slug: "{{kebab-case-slug}}"
version: "0.1.0"
status: draft            # draft | in-review | approved
profile: mvp             # prototype | mvp | production | enterprise
date: "{{YYYY-MM-DD}}"
owners: ["{{name}}"]
stack:
  frontend: "{{e.g. Next.js 15 + Tailwind v4 + shadcn/ui}}"
  backend: "{{e.g. FastAPI + SQLAlchemy 2}}"
  database: "{{e.g. PostgreSQL 16 (Supabase)}}"
  migrations: "{{e.g. Alembic}}"
  api_contract: "{{openapi | graphql | trpc | none}}"
  agents: "{{e.g. OpenAI Agents SDK | none}}"
  infra: "{{e.g. Docker Compose, GitHub Actions}}"
features:                # subset of: tenancy, audit, money, ui, ai-agents, api-contract, database, posted-documents, offline, compliance
  - ui
  - database
layout:                  # folder for each independently verifiable part (used by bootstrap lanes)
  api: apps/api
  web: apps/web
  agents: apps/agents
  infra: infra
  client: packages/api-client
phases: 4
---

# {{Project name}} — Product Requirements & Technical Specification

## 0. Document Control

### 0.1 Purpose and audience
_Who reads this (developers, product owner, QA, stakeholders) and how it is used (this PRD is the source of truth for scope; changes go through §25)._

### 0.2 Revision history
| Version | Date | Author | Summary of change | Sections touched |
| --- | --- | --- | --- | --- |
| 0.1.0 | {{date}} | {{name}} | Initial draft from discovery interview | all |

### 0.3 Assumptions ledger
_Every decision the user delegated ("you decide") or that was inferred. Each row can be challenged later._
| ID | Assumption | Basis | Owner to confirm |
| --- | --- | --- | --- |
| A-001 | | | |

### 0.4 Open questions
| ID | Question | Blocks (section/phase) | Owner | Status |
| --- | --- | --- | --- | --- |
| Q-001 | | | | open |

### 0.5 Glossary
| Term | Meaning in this product |
| --- | --- |

---

## 1. Executive Summary
_The product in 2-3 paragraphs: who it serves, the problem, the outcome, the delivery profile (§0 `profile`), and how this document is meant to be used. State the deployment model and the one or two things that make this product different._

## 2. Product Objectives
_Bulleted, testable objectives (8-12). Each one starts with a verb and could be checked at UAT._
- 

### 2.1 Success metrics
| Metric | Baseline | Target | How measured |
| --- | --- | --- | --- |

### 2.2 Out of scope
_Explicit non-goals. Anything here needs a change request (§25) to enter scope._

## 3. Technology & Architecture

### 3.1 Stack decision record
| Layer | Required technology / standard | Why this choice | Considered and rejected |
| --- | --- | --- | --- |
| UI | | | |
| Backend | | | |
| Business logic | | | |
| ORM / data access | | | |
| Database | | | |
| Migrations | | | |
| API | | | |
| Authentication | | | |
| Authorization | | | |
| Background jobs | | | |
| Cache / queue | | | |
| Search | | | |
| File storage | | | |
| AI / agents | | | |
| Observability | | | |
| CI/CD | | | |
| Hosting / deployment | | | |
| Containers | | | |
| Testing | | | |

### 3.2 Considered and deferred
_Infrastructure deliberately not adopted yet (Redis, queues, search engine, Kubernetes, microservices…) and the measurable trigger that would bring it in._
| Technology | Why not now | Trigger to adopt |
| --- | --- | --- |

### 3.3 Architecture overview
_Deployment units, how they talk, and which unit owns data. Include a diagram (Mermaid or ASCII)._
```
Browser -> Web app -> API (sole owner of business logic and data access) -> Database
                          ^
                          +-- Agents/workers call the API as clients; they never hold database credentials.
```

### 3.4 Repository layout
_Real folder tree. It must match `layout` in the front matter._

### 3.5 Multi-tenancy and scoping
_Tenant/company/branch model. How scope is enforced centrally (filter/row-level security), and how a deliberate bypass is reviewed._

### 3.6 Environments and deployment models
_Local, CI, staging, production. Cloud / on-premise / hybrid. Configuration and secrets handling._

### 3.7 Architectural constraints (non-negotiable)
_5-10 statements that no task may violate. Each becomes an entry in `AGENTS.md` and a check (test, lint or `verify.sh` step)._
1. 

## 4. Application Navigation / Main Menu
_Menu tree per role. Module → screens. Which items are hidden vs disabled for unauthorized users._

## 5. Form & Screen Specification

### 5.1 Mandated form layout
_The one layout every form follows, e.g. Header/Title + status → Filters or master fields → Detail grid → Totals → Actions → Audit/status panel._

### 5.2 Form register
| ID | Form / screen | Module | Type (master, transaction, list, settings, report) | Roles | Priority | Phase |
| --- | --- | --- | --- | --- | --- | --- |
| F-001 | | | | | P0 | 1 |

### 5.3 Field-level specifications
_One subsection per form that has business fields: field, type, required, validation, default, source. **Never add a field that is not listed here without a change request (§25).**_

#### F-001 {{Form name}}
| Field | Type | Required | Validation / rule | Notes |
| --- | --- | --- | --- | --- |

## 6. Key Screen — Detailed Requirements
_For the one or two screens that carry the product (e.g. checkout screen, editor, kanban board): layout regions, keyboard/touch behaviour, response-time budget, error states, hardware, shortcuts._

## 7. Dashboards
| ID | Dashboard | Role | KPIs (each drills down to records) | Refresh | Phase |
| --- | --- | --- | --- | --- | --- |
| D-001 | | | | | |

## 8. Dashboard UI Standard
_KPI card anatomy, chart types allowed, filters (date range, branch), drill-down rule, empty/loading/error states, permission and scope awareness._

## 9. Reports
| ID | Report | Module | Filters | Export | Roles |
| --- | --- | --- | --- | --- | --- |
| R-001 | | | | | |

## 10. Core Business Workflows
_One subsection per workflow with numbered steps, actors, states and what is written to the database and audit log at each step._
### W-001 {{Workflow}}
1. 
- **State machine:** `draft -> submitted -> approved -> posted -> reversed`
- **Failure paths:** 

## 11. Offline & Synchronization
_Mandatory or optional? Data retained locally, sync queue states (pending, sent, acknowledged, failed, conflict), idempotency key per transaction, retry/backoff, conflict policy, monitor screen. "Not applicable — <reason>" if online-only._

## 12. Database / Data Model

### 12.1 Domains and representative tables
| Domain | Representative tables |
| --- | --- |
| Organization | |
| Security | users, roles, permissions, role_permissions, sessions, audit_logs |

### 12.2 Conventions
_Naming (`lower_snake_case`, plural tables), primary keys (UUID/bigint), soft delete, timestamps, money type and precision, optimistic concurrency, indexing rule, tenant columns._

### 12.3 Entity detail
_Per key entity: columns, types, constraints, indexes, relationships. The ERD is generated from the live schema; this section states intent._

### 12.4 Migration policy
_Every schema change ships as a migration in the same PR; migrations are never edited after merge; a CI check fails when the model has changes not captured in a migration._

### 12.5 Data retention, seed data, sample data

## 13. API Requirements

### 13.1 Conventions
_Versioned base path (`/api/v1`), REST naming, pagination/filter/sort parameters, idempotency header, error format (RFC 7807), correlation ID, rate limits, OpenAPI as contract, generated client._

### 13.2 Endpoint register
| Area | Endpoint | Methods | Permission | Notes |
| --- | --- | --- | --- | --- |
| Auth | `/api/v1/auth` | POST | public | login, refresh, logout, me |

### 13.3 Integrations (external)
| ID | System | Direction | Protocol | Auth | Failure handling | Phase |
| --- | --- | --- | --- | --- | --- | --- |
| I-001 | | | | | | |

## 14. Security & Audit
- HTTPS in all non-development environments.
- Role-based authorization enforced by the API (the UI hiding an action is convenience, not security).
- No credentials or secrets in source control; `.env.example` holds keys with empty values.
- Passwords stored only with an approved password-hashing algorithm; lockout and rate limiting on authentication.
- Validation on all user input and API payloads; parameterized queries or the ORM only.
- Sensitive data masked in logs.
### 14.1 Audited actions
_List every action that must write an audit row (who, what, when, before/after, source)._
### 14.2 Roles and permission matrix
| Role | Modules / screens | Actions (view, create, edit, delete, approve, export, post, reverse) |
| --- | --- | --- |
### 14.3 Data protection and privacy
_Classification, encryption at rest/in transit, retention, subject-rights handling, backups encryption._
### 14.4 Threat notes
_Top 5 threats for this product and the control for each._

## 15. AI-Assisted Development Protocol
| Step | Developer / agent requirement |
| --- | --- |
| 1. Requirement | A small, testable story with acceptance criteria |
| 2. Context | Supply structure, conventions, constraints (`context/` folder) |
| 3. Design | Agree database/API/UI design before large generation (`/architect`) |
| 4. Generate | Scaffolding, implementation, refactoring, tests |
| 5. Review | A human reviews all generated code, queries, security, error handling (`/review`) |
| 6. Test | Acceptance tests written first and passing; `scripts/verify.sh` green |
| 7. PR | Requirement, test evidence, migration notes |
| 8. Merge | Only approved, passing PRs reach protected branches |

The development team remains accountable for architecture, security, correctness and maintainability. AI tooling is never given unrestricted production credentials or unrestricted database write access.

## 16. UI/UX Standards
_Layout, density, typography, colour tokens, forms and validation, data grid rules, feedback, accessibility (target level), responsive breakpoints, keyboard support, the four states (loading, empty, error, unauthorized), formatting via a single module._

## 17. Performance Requirements
| Area | Target / requirement | How verified |
| --- | --- | --- |
| Standard interaction | | |
| Search | | |
| Transaction posting | | |
| Reports | Heavy reports must not block transactional operations | |
| Concurrency | | |
| Database | | |

## 18. Backup & Disaster Recovery
_RPO/RTO, backup frequency and retention, encryption, restore procedure, **scheduled restore test**, failover, who is on call._

## 19. Testing & Acceptance
| Test level | Scope | Tooling |
| --- | --- | --- |
| Unit | Domain rules, calculations | |
| Architecture | Layer dependencies, every endpoint has an authorization decision, tenant scoping on every entity | |
| Integration | API + database + auth + scoping + audit (real database) | |
| Component / UI | Forms, validation, permissions, responsive behaviour | |
| E2E | Critical workflows end to end | |
| Offline | Disconnect, transact, reconnect, sync, conflict | |
| Performance | Hot paths against §17 | |
| Security | Dependency scan, secret scan, authz tests | |

## 20. Acceptance Criteria for Forms
_Checklist every form passes: layout per §5.1, field validation, inline errors, permissions, audit panel, four states, keyboard flow, responsive._

## 21. Acceptance Criteria for Dashboards
_Every KPI drills down; numbers reconcile with source data; scoped to the user's permissions; loads within target._

## 22. Phased Delivery Plan
| Phase | Scope | Exit criteria (a test a person can run) |
| --- | --- | --- |
| 0 | Foundation: repo, CI, migrations, auth, tenancy/audit skeleton, design tokens | Foundation approved + CI green + login works end to end |
| 1 | | |

## 23. Required Deliverables
- Complete source code and full repository history
- Database migrations and ERD / database documentation
- API documentation (OpenAPI)
- All forms and dashboards listed in §5 and §7
- Unit, integration and E2E tests
- Deployment scripts and environment configuration guide
- Backup/restore guide
- Administrator manual and user manual
- _(add project-specific: hardware guide, sync operating guide, training material)_

## 24. Definition of Done
- Requirement implemented and demonstrated
- Database migration included
- API and UI completed
- Validation and authorization implemented
- Audit requirements implemented
- Automated tests added and passing; `scripts/verify.sh` passes
- No critical/high unresolved defects
- Code reviewed by a human developer (including AI-generated code)
- Documentation updated
- UAT passed

## 25. Change Control
Any feature, form, report, integration or workflow not in this PRD is handled by a change request recording: scope, business reason, effort, impact on schedule and cost, affected sections, decision, approver. Approved changes are recorded in §0.2 and, for stack or architecture changes, as an ADR in `docs/adr/`.
### 25.1 Change request log
| CR | Date | Requester | Summary | Sections | Decision | Approver |
| --- | --- | --- | --- | --- | --- | --- |

## 26. Initial Feature Priority
| Priority | Meaning | Items |
| --- | --- | --- |
| P0 — Mandatory MVP | Cannot ship without | |
| P1 — Commercial release | | |
| P2 — Expansion | | |
| P3 — Differentiation | | |

## 27. Final Product Structure
_Module map: modules, their screens, their tables, their APIs — one table so nothing is orphaned._

## 28. Approval
| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Product owner | | | |
| Technical lead | | | |

## 29. Visual UI / UX Wireframes — Dashboards
_One subsection per dashboard in §7, numbered 29.1, 29.2 … Use an ASCII wireframe (or a linked image). KPI names must match §7._

### 29.1 {{Dashboard name}}
```
+--------------------------------------------------------------+
| KPI 1        | KPI 2        | KPI 3        | KPI 4            |
+--------------------------------------------------------------+
| Chart / trend                | Top-N list (drill-down)       |
+--------------------------------------------------------------+
```

## 30. Visual Form Wireframes
_One subsection per key form in §5.2, numbered 30.1, 30.2 … Field names must match §5.3 exactly. Follow the mandated layout in §5.1._

### 30.1 {{Form name}}
```
+--------------------------------------------------------------+
| Title                                             [status]   |
+--------------------------------------------------------------+
| Master fields                                                |
+--------------------------------------------------------------+
| Detail grid                                                  |
+--------------------------------------------------------------+
| Totals                                                       |
+--------------------------------------------------------------+
| [Save] [Post] [Cancel]                                       |
+--------------------------------------------------------------+
| Audit / status panel                                         |
+--------------------------------------------------------------+
```

## 31. Visual Design Rules for Implementation
_Rules the implementing agent must follow: tokens only (no hard-coded colours), spacing scale, component reuse (check the UI registry first), density, iconography, motion._

## 32. UI Acceptance Checklist
- [ ] Layout matches §5.1
- [ ] Every field is in §5.3 (no invented fields)
- [ ] Inline validation, actionable error messages
- [ ] Unauthorized actions hidden or disabled; API still enforces
- [ ] Loading, empty, error, unauthorized states present
- [ ] Keyboard navigation complete
- [ ] Responsive on the target devices
- [ ] Audit/status panel present where required

## 33. Note on Final UI Design
_Is the visual identity final or provisional? If provisional, only the token values change later; workflow and information architecture do not._

## 34. Mandatory Compliance / Regulatory Integration Requirement
_Tax, e-invoicing, privacy or industry rules that are legally required. "Not applicable — <reason>" if none. If applicable, this is **P0** and is scheduled into an early phase, never deferred._

### 34.1 Integration Scope
### 34.2 Transaction Flow
### 34.3 Integration Statuses
| Status | Meaning | Next allowed states |
| --- | --- | --- |
### 34.4 Integration Form
_Screen(s) that show submission state, retries and errors (register them in §5.2)._
### 34.5 Failure Handling
_Retry/backoff, queueing while the authority is unreachable, what the operator sees, manual override rules._
### 34.6 Reporting & Reconciliation
### 34.7 Security Requirements
_Credentials storage, signing, certificates, IP allow-listing, audit._
### 34.8 Acceptance Criteria

## 35. Mandatory P0 Compliance Requirement
_Restate the compliance items that block go-live and the phase that delivers each._

## 36. Mandatory Agentic AI Architecture
_Include only when the product has AI features; otherwise write "Not applicable — no AI features in scope" under this heading and keep the numbering._

### 36.1 Agentic AI Product Vision
_Jobs to be done, who benefits, what "good" looks like._
### 36.2 Agentic AI Architecture
_User → Agent → approved tool → API/business service → validated command/query → database. The AI service is a client of the API._
### 36.3 AI Must Not Have Direct Database Authority
_The AI layer shall not hold database credentials or run arbitrary SQL. All data access and actions pass through approved tools that enforce tenant, scope and user permissions; financial/stock commands run inside controlled business transactions; explanations are traceable to the tools and data used._
### 36.4 AI Tool / Function Layer
| Tool | Purpose | Read/Write | Required permission | Approval level |
| --- | --- | --- | --- | --- |
### 36.5 Specialized Agents
| Agent | Responsibility | Tools it may call | Autonomy level |
| --- | --- | --- | --- |
### 36.6 AI Autonomy Levels
_L1 explain · L2 recommend · L3 draft (approval required) · L4 act within limits · L5 fully autonomous. State the level per agent and the promotion criteria._
### 36.7 AI Approval Center
### 36.8 AI Command Center Dashboard
### 36.9 AI Agent Activity / Audit Form
_Every run: who asked, which agent, tools called, inputs/outputs, approvals, cost, outcome._
### 36.10 Agent Requirements — {{Agent 1, e.g. Inventory}}
### 36.11 Agent Requirements — {{Agent 2}}
### 36.12 Agent Requirements — {{Agent 3}}
### 36.13 Agent Requirements — {{Agent 4}}
### 36.14 Agent Requirements — {{Agent 5}}
### 36.15 Agent Requirements — {{Agent 6, e.g. Compliance}}
### 36.16 Anomaly Detection Agent
### 36.17 Daily Autonomous Business Brief
### 36.18 Agent Guardrails
_Spend and rate limits, blocked actions, prompt-injection handling, PII handling, human-in-the-loop points._
### 36.19 AI Security & Privacy
### 36.20 AI Testing Requirements
_Authorization, data isolation, action safety, prompt robustness, schema validation, transaction integrity, audit._
### 36.21 AI-Assisted Development of the AI Layer
### 36.22 Recommended AI Technology Integration
_Agent framework, model providers, vector store, evaluation tooling, observability._
### 36.23 AI Phase Roadmap
### 36.24 Agentic AI Acceptance Criteria

## 37. Updated Master Priority
_Consolidated priority list after all mandatory requirements (§34-§36) are folded in._

## 38. Final Architectural Principle
_One paragraph that settles disputes: e.g. "The API is the only owner of business logic and data. Every client, including AI, is a client."_

---

## Appendix A — Decision log
| Date | Decision | Reason | Alternatives considered |
| --- | --- | --- | --- |

## Appendix B — Risks
| ID | Risk | Likelihood | Impact | Mitigation | Owner |
| --- | --- | --- | --- | --- | --- |

## Appendix C — Cost and infrastructure profile
_Monthly running-cost estimate by service and by phase (free tier limits called out), so the budget answer from discovery stays visible._
| Service | Tier / plan | Limit that matters | Est. monthly cost |
| --- | --- | --- | --- |
