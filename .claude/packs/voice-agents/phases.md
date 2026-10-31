# Voice agents — phases

Phase 0 and Phase 1 are a production MVP: the smallest thing real users can rely on. Anything bigger is deferred with its trigger.

## Phase 0

- Channel setup (number or WebRTC room) and a hello-world call — Accept: A test call connects and the agent answers
- Latency and cost instrumentation per turn — Accept: Each call logs per-turn latency and cost; a cap stops runaway calls
- Evaluation set of recorded calls — Accept: The set replays offline and reports task success

## Phase 1

- One complete call flow with confirmation of captured data — Accept: Names, numbers and dates are read back; wrong data can be corrected by the caller
- Barge-in, silence and noise handling — Accept: Each behaviour has a recorded test case that passes
- Human handoff and keypad fallback — Accept: A forced trigger transfers the call with context
- Consent notice, redaction and retention — Accept: The notice plays; a transcript in the test set contains no personal data after redaction

## Deferred

- Custom or cloned voice — Trigger: Brand requires it and the licence and consent for the voice are in hand
- Outbound campaigns — Trigger: Inbound flow meets its success target and legal review of outbound calling is done
- Multiple languages beyond the first — Trigger: A second language is committed and has its own recorded evaluation set
- Sentiment analytics — Trigger: Handoff triggers prove insufficient in the evaluation set
