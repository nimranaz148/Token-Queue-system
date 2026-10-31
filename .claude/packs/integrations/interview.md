# Third-party integrations (Salesforce, OAuth providers, payments, marketplaces, email) — technical interview

Ask only what changes the build. Each question carries a recommendation and a free-tier default; the user answers yes or names a change.

## Q1. Which external systems, and in which direction does data flow?

- **Recommend:** List each vendor with the direction (read, write, both) and the owner of the data. Start with one direction.
- **Free default:** Vendor sandbox or developer account for every vendor.

## Q2. Does the vendor offer a sandbox and published rate limits?

- **Recommend:** Do not start building against production. If there is no sandbox, record a fixture-based plan and the extra risk.
- **Free default:** None needed.

## Q3. How does authentication to the vendor work?

- **Recommend:** OAuth 2.0 authorisation code with PKCE for user-delegated access; client credentials for server-to-server; store tokens encrypted.
- **Free default:** None needed.

## Q4. Does the vendor call us (webhooks)?

- **Recommend:** Verify signatures, reject replays, respond quickly and process asynchronously.
- **Free default:** None needed.

## Q5. What happens when the vendor is down or slow?

- **Recommend:** Define degraded behaviour per feature: queue and retry, show stale data with a notice, or fail clearly.
- **Free default:** None needed.

## Q6. Is a ready-made skill available for this vendor?

- **Recommend:** Search the skills sources first; if there is none, generate a project-local integration skill from the vendor's current documentation and cite the URL and date.
- **Free default:** None needed.

