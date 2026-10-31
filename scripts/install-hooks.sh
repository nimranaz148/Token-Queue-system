#!/usr/bin/env bash
# One-time per clone: point git at the versioned hooks in .githooks/.
set -euo pipefail
git config core.hooksPath .githooks
echo "Git hooks enabled (.githooks/pre-push runs scripts/verify.sh)."
