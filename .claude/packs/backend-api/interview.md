# Backend API (framework-agnostic) — technical interview

Ask only what changes the build. Each question carries a recommendation and a free-tier default; the user answers yes or names a change.

## Q1. Language and framework?

- **Recommend:** The one the team already ships in; otherwise FastAPI (Python), ASP.NET Core (C#) or NestJS (TypeScript): all have OpenAPI support and good test tooling.
- **Free default:** All free and open source.

## Q2. Database?

- **Recommend:** PostgreSQL: relational, strong constraints, free managed tiers.
- **Free default:** Managed free tier or a container for local work.

## Q3. How are schema changes managed?

- **Recommend:** A migration tool that generates and applies versioned migrations (Alembic, EF Core migrations, Prisma Migrate, Flyway), checked in CI against a real database.
- **Free default:** None needed.

## Q4. Authentication for API clients?

- **Recommend:** Short-lived access tokens with refresh for first-party apps; API keys only for server-to-server use.
- **Free default:** None needed.

## Q5. API style and contract?

- **Recommend:** REST with an OpenAPI document as the contract, a generated client for the front end, and a drift check in the fast tier.
- **Free default:** None needed.

## Q6. Multiple tenants or branches?

- **Recommend:** If yes, scope every query centrally and deny by default; decide before the first table is created.
- **Free default:** None needed.

## Q7. Background work, files, search?

- **Recommend:** Not for the MVP: add a queue, object storage or a search engine only when a measured need appears.
- **Free default:** Run synchronously and on the database until the trigger.

