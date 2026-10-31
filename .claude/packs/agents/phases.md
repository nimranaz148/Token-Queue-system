# AI agents (multi-agent frameworks) — phases

Phase 0 and Phase 1 are a production MVP: the smallest thing real users can rely on. Anything bigger is deferred with its trigger.

## Phase 0

- Agent service skeleton, separate from the API, with no database credentials — Accept: The service starts; its environment contains no database variable (checked by a test)
- Tool catalogue with schemas, permissions and a test per tool — Accept: A forbidden call is rejected; each tool has a unit test
- Evaluation harness with a first golden set — Accept: The suite runs in the fast tier against recorded model responses

## Phase 1

- First agent flow end to end with human approval on side effects — Accept: An approved action runs; a rejected action does not; the trace shows both
- Run caps, spend cap and kill switch — Accept: Exceeding a cap stops the run with a clear message; the kill switch works without a deploy
- Tracing with redaction — Accept: A trace of a run contains no personal data from the test fixtures

## Deferred

- Long-term memory — Trigger: Users repeat context across sessions and a retrieval test shows it improves outcomes
- Multiple cooperating agents — Trigger: A single agent fails the golden set because of context length or role conflict
- Fine-tuning — Trigger: Prompting and retrieval cannot reach the target on the golden set
- Autonomous execution without approval — Trigger: The golden set shows a stated success rate over a stated number of runs
