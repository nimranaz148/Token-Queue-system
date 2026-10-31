# DevOps and infrastructure — phases

Phase 0 and Phase 1 are a production MVP: the smallest thing real users can rely on. Anything bigger is deferred with its trigger.

## Phase 0

- CI workflow per lane calling scripts/verify.sh, with secret and dependency scans — Accept: A deliberately broken commit turns CI red; the clean tree is green
- Branch protection and required checks — Accept: A direct push to main is refused
- Production and preview environments on the chosen host — Accept: A pull request creates a preview; merging deploys production

## Phase 1

- Monitoring, alerting and a first runbook — Accept: A forced failure pages the named person within the stated time
- Backups and one timed restore — Accept: Restore completes within the recovery target
- Practised rollback — Accept: The previous version is restored in under the recovery target
- Budget alerts — Accept: A test alert reaches the named person

## Deferred

- Staging environment separate from previews — Trigger: Paying users exist or a release needs soak time
- Infrastructure as code — Trigger: A second environment must be kept identical to the first
- Autoscaling and load balancing — Trigger: Utilisation stays above the PRD target for a week
- Multi-region and disaster-recovery drills — Trigger: A written availability or compliance requirement the single region cannot meet
- Kubernetes — Trigger: More than a handful of services need independent scaling and a platform team exists to run it
