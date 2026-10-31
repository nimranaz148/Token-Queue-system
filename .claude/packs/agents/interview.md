# AI agents (multi-agent frameworks) — technical interview

Ask only what changes the build. Each question carries a recommendation and a free-tier default; the user answers yes or names a change.

## Q1. Which agent framework?

- **Recommend:** The vendor SDK that matches the model provider (OpenAI Agents SDK, Claude Agent SDK) for the MVP; a graph framework only when you need explicit multi-step control flow.
- **Free default:** Pay-per-use API; set a monthly cost ceiling first.

## Q2. What can each agent do (the tool catalogue)?

- **Recommend:** Write every tool with its inputs, outputs, side effects and the permission it needs; start with read-only tools.
- **Free default:** None needed.

## Q3. Which actions need a human to approve?

- **Recommend:** Anything destructive, financial or customer-visible, until evaluation shows it is safe.
- **Free default:** None needed.

## Q4. What data may the agent see?

- **Recommend:** Only through the API with the caller's identity; the agent service holds no database credentials.
- **Free default:** None needed.

## Q5. How will quality be measured?

- **Recommend:** A golden set of real cases with expected outcomes, run in CI; add cases whenever the agent fails in use.
- **Free default:** A small hand-written set is enough to start.

## Q6. What are the cost and latency ceilings?

- **Recommend:** A per-run token and step cap and a per-day spend cap with an alert.
- **Free default:** None needed.

