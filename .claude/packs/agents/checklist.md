# AI agents (multi-agent frameworks) — checklist

Every item must be answered in the PRD before Phase 1 exits. Each becomes a requirement and a candidate acceptance test.

- [ ] C-A-01 Every tool has the least privilege it needs, and a forbidden call is rejected, not merely discouraged in the prompt.
- [ ] C-A-02 The agent service has no database credentials; it reaches data only through the API with the caller's identity.
- [ ] C-A-03 Text returned by tools, web pages and documents is treated as untrusted and cannot change the agent's instructions or permissions.
- [ ] C-A-04 Each run has a maximum number of steps, tokens and wall-clock time, and ends with a clear message when a cap is hit.
- [ ] C-A-05 Destructive and customer-visible actions require explicit human approval until evaluations justify removing it.
- [ ] C-A-06 A golden-case evaluation suite runs in CI; a regression fails the build.
- [ ] C-A-07 Structured outputs are validated against a schema; invalid output is retried once and then escalated.
- [ ] C-A-08 Traces record prompts, tool calls and results with personal data redacted, and are kept for a stated period.
- [ ] C-A-09 Model errors, rate limits and timeouts have a defined fallback (retry, smaller model, human).
- [ ] C-A-10 Prompts and tool descriptions are versioned in the repository and changes go through review.
- [ ] C-A-11 A per-day spend cap exists with an alert and an automatic stop.
- [ ] C-A-12 A kill switch disables the agent without a deploy.
- [ ] C-A-13 Personal data sent to the model provider is identified and covered by the provider terms in use.
