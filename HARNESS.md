# HARNESS.md — the ratchet

The model learns nothing between runs. This file is where the project learns.

**Rule:** when the agent makes a mistake, do not only fix the work. Name the failure class, change the surface that class lives on so the mistake becomes impossible, record it below, and re-run `bash scripts/harness-check.sh`. A harness change you did not re-check is a guess.

## The four failure classes

| Class | The sign | Fix lives in |
| --- | --- | --- |
| **Context** | It did not know: wrong convention, missed constraint, reinvented decision | `AGENTS.md`, a skill, a tool description |
| **Constraint** | It did something it should never have been able to do | `.claude/settings.json` deny/ask rules, sandbox, branch protection |
| **Verification** | Bad work was called done: tests not run, claim unchecked | a `verify.sh` step, a hook, required CI, the typed `/review` verdict |
| **Planning** | Right pieces, wrong order or size: wandering, bundled changes | a smaller task in `context/build-plan.md`, a step cap, a split |

Two failures with the same shape should be impossible. If you see a second, the first was classified wrong.

## Log

| Date | What went wrong (one sentence) | Class | The fix, and the surface it went on |
| --- | --- | --- | --- |
| | | | |
