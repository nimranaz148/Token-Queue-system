# Backend API (framework-agnostic) — phases

Phase 0 and Phase 1 are a production MVP: the smallest thing real users can rely on. Anything bigger is deferred with its trigger.

## Phase 0

- Scaffold the API with lint, format, typecheck and a health endpoint — Accept: The service starts from a clean clone; the health endpoint answers
- Database foundation and first migration — Accept: Migration applies to an empty database; the migration check passes in the fast tier
- Authentication and authorisation skeleton — Accept: Login works; a role without access gets 403; one test per role
- OpenAPI contract and generated client with a drift check — Accept: The drift check fails when an endpoint changes without regeneration

## Phase 1

- First vertical slice: one resource with create, read, update, delete — Accept: Validation, authorisation and pagination are tested; error format matches the contract
- Tenant or branch scoping (if the PRD has it) — Accept: A test proves tenant A cannot read or write tenant B; no tenant context returns nothing
- Structured logging, request ids and error reporting — Accept: A failed request can be traced from the response id to the log line
- Backups and one timed restore — Accept: The restore completes within the PRD recovery target

## Deferred

- Background job queue — Trigger: A task takes longer than a request should wait, or must retry independently of the request
- Caching layer (Redis or similar) — Trigger: A measured query or endpoint exceeds its target after indexing
- Search engine — Trigger: Database search cannot meet the PRD response target at real data volume
- Read replicas — Trigger: Reads saturate the primary after caching
- Microservices split — Trigger: Two teams cannot deploy independently because of the monolith
