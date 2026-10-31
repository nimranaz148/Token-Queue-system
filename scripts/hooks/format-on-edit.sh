#!/usr/bin/env bash
# Claude Code PostToolUse hook (Edit|Write|MultiEdit) — see .claude/settings.json.
#
# Formats and lints ONLY the file the agent just touched, in seconds, so
# style/EOL/lint failures never survive to scripts/verify.sh or CI.
# Auto-fixes what it can; exits 2 with the remaining problems on stderr,
# which Claude Code feeds straight back to the agent to fix.

set -uo pipefail

INPUT="$(cat)"
FILE="$(printf '%s' "$INPUT" | node -e '
  let s = ""; process.stdin.on("data", d => s += d).on("end", () => {
    try { process.stdout.write(JSON.parse(s).tool_input?.file_path ?? ""); } catch { }
  });' 2> /dev/null)"

[ -n "$FILE" ] || exit 0
# Windows paths (C:\...) arrive verbatim from Claude Code; normalise for Git Bash.
command -v cygpath > /dev/null 2>&1 && FILE="$(cygpath -u "$FILE")"
[ -f "$FILE" ] || exit 0

ROOT="$(git -C "$(dirname "$FILE")" rev-parse --show-toplevel 2> /dev/null)" || exit 0
command -v cygpath > /dev/null 2>&1 && ROOT="$(cygpath -u "$ROOT")"
REL="$(realpath --relative-to="$ROOT" "$FILE" 2> /dev/null || echo "$FILE")"
cd "$ROOT" || exit 0

PROBLEMS=""

case "$REL" in
  apps/web/*.ts|apps/web/*.tsx|apps/web/*.js|apps/web/*.mjs)
    NODE_REL="${REL#apps/web/}"
    OUT="$(cd apps/web && npx --no-install eslint --fix "$NODE_REL" 2>&1)" || PROBLEMS="$OUT"
    ;;
  apps/api/*.py)
    if command -v uv > /dev/null 2>&1; then
      PY_REL="${REL#apps/api/}"
      OUT="$(cd apps/api && uv run --quiet ruff check --fix "$PY_REL" 2>&1)" || PROBLEMS="$OUT"
    fi
    ;;
  packages/api-client/src/generated/*)
    PROBLEMS="Generated from the OpenAPI contract; never hand-edit."
    ;;
esac

if [ -n "$PROBLEMS" ]; then
  printf 'Lint problems in %s — fix them now:\n%s\n' "$REL" "$PROBLEMS" >&2
  exit 2
fi
exit 0
