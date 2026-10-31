# Voice agents — checklist

Every item must be answered in the PRD before Phase 1 exits. Each becomes a requirement and a candidate acceptance test.

- [ ] C-VA-01 Per-turn latency is measured and the 95th percentile is within the stated target.
- [ ] C-VA-02 Barge-in works: the agent stops speaking when the caller starts.
- [ ] C-VA-03 Silence, background noise and cross-talk have defined behaviour (re-prompt, then handoff).
- [ ] C-VA-04 Recording and consent notices follow the law of every target jurisdiction, and the consent is logged.
- [ ] C-VA-05 Personal data in transcripts and logs is redacted, with a stated retention period.
- [ ] C-VA-06 Names, numbers, dates and addresses are read back and confirmed before any action depends on them.
- [ ] C-VA-07 A human handoff and a keypad (DTMF) fallback exist and are tested.
- [ ] C-VA-08 Tool calls with side effects need explicit confirmation from the caller.
- [ ] C-VA-09 Cost per minute is measured; a daily spend cap and concurrency limit exist.
- [ ] C-VA-10 Accents, noisy audio and each supported language have recorded test calls in the evaluation set.
- [ ] C-VA-11 Provider outage degrades gracefully: a clear message and a way to reach a person.
- [ ] C-VA-12 A set of real, anonymised calls is replayed in CI or nightly to catch regressions.
