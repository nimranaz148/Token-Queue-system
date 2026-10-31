#!/usr/bin/env bash
# Claude Code Stop hook — see .claude/settings.json.
#
# When the agent finishes a turn with uncommitted code changes, run
# scripts/verify.sh (only the lanes those changes affect). On failure, exit 2
# so the agent keeps working on the reported failures instead of stopping —
# "done" means verify passed, not "the agent believes it works".
#
# Skips cheaply when nothing changed since the last green run, so chat-only
# turns cost nothing. Set SKIP_VERIFY=1 to disable for a session.
# Always the FAST tier: slow checks (integration tests, builds, scans) run in CI and /review.

set -uo pipefail

[ "${SKIP_VERIFY:-}" = "1" ] && exit 0

INPUT="$(cat)"
# Already continuing because of this hook: let the agent stop and report
# rather than loop forever on something it cannot fix.
ACTIVE="$(printf '%s' "$INPUT" | node -e '
  let s = ""; process.stdin.on("data", d => s += d).on("end", () => {
    try { process.stdout.write(String(JSON.parse(s).stop_hook_active === true)); } catch { process.stdout.write("false"); }
  });')"

ROOT="$(git rev-parse --show-toplevel 2> /dev/null)" || exit 0
cd "$ROOT" || exit 0

# Fingerprint of the working tree (tracked diff + untracked files). Docs-only
# changes never trigger a lane in verify.sh, so they fall through fast.
STAMP_FILE="$(git rev-parse --git-dir)/verify-stamp"
FINGERPRINT="$( { git rev-parse HEAD; git diff HEAD; git ls-files --others --exclude-standard | xargs -r sha1sum 2> /dev/null; } | sha1sum | cut -d' ' -f1)"

[ -f "$STAMP_FILE" ] && [ "$(cat "$STAMP_FILE")" = "$FINGERPRINT" ] && exit 0

OUTPUT="$(VERIFY_TIER=fast bash scripts/verify.sh 2>&1)"
STATUS=$?

if [ $STATUS -eq 0 ]; then
  echo "$FINGERPRINT" > "$STAMP_FILE"
  exit 0
fi

if [ "$ACTIVE" = "true" ]; then
  # Second failure in a row: stop, but make sure the human sees it.
  printf 'scripts/verify.sh is still failing — reporting to the developer instead of retrying:\n%s\n' "$(printf '%s' "$OUTPUT" | tail -25)"
  exit 0
fi

{
  echo "scripts/verify.sh FAILED — the task is not done. Fix these, do not work around them:"
  printf '%s\n' "$OUTPUT" | grep -E '^(✗|⚠|verify:)' | awk '!seen[$0]++' || true
  echo ""
  echo "Detail (last 60 lines; full log: \${TMPDIR:-/tmp}/verify-last.log):"
  printf '%s\n' "$OUTPUT" | tail -60
} >&2
exit 2
