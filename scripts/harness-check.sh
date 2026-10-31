#!/usr/bin/env bash
# scripts/harness-check.sh — the harness's own regression check.
#
# Run it after ANY change to .claude/settings.json, scripts/verify.sh, scripts/hooks/ or AGENTS.md.
# A harness change you did not re-check is a guess. Exit 0 = intact; exit 1 prints, per problem,
# what is wrong and the exact next step.
set -uo pipefail
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT" || exit 1
FAIL=0
bad() { echo "✗ harness: $1"; echo "  next: $2"; FAIL=1; }

if [ ! -f scripts/verify.sh ]; then
  bad "scripts/verify.sh is missing" "re-run /bootstrap, or copy scripts/ from the harness templates"
elif ! bash -n scripts/verify.sh 2>/dev/null; then
  bad "scripts/verify.sh has a syntax error" "run 'bash -n scripts/verify.sh' and fix the line it reports"
elif ! bash scripts/verify.sh --all --list > /dev/null 2>&1; then
  bad "scripts/verify.sh cannot list its lanes" "run 'bash scripts/verify.sh --all --list' and fix the error it prints"
fi

[ -f scripts/check_verdict.py ] || bad "scripts/check_verdict.py is missing" "copy it from the harness templates (templates/scripts/check_verdict.py)"

if [ -f scripts/hooks/verify-on-stop.sh ] && ! grep -q 'VERIFY_TIER=fast' scripts/hooks/verify-on-stop.sh; then
  bad "the Stop hook does not pin the fast tier" "set 'VERIFY_TIER=fast' on the verify.sh call in scripts/hooks/verify-on-stop.sh"
fi

if [ ! -f .claude/settings.json ]; then
  bad ".claude/settings.json is missing" "copy templates/.claude/settings.json into .claude/settings.json"
elif command -v node > /dev/null 2>&1; then
  PROBLEMS="$(node -e '
    let s;
    try { s = JSON.parse(require("fs").readFileSync(".claude/settings.json", "utf8")); }
    catch (e) { console.log("settings.json is not valid JSON: " + e.message); process.exit(1); }
    const errs = [];
    const deny = (s.permissions && s.permissions.deny) || [];
    if (!deny.some(d => d.includes(".env"))) errs.push("no deny rule for .env files");
    if (!deny.some(d => /push (--force|-f)/.test(d))) errs.push("no deny rule for force-push");
    const h = s.hooks || {};
    if (!h.Stop) errs.push("no Stop hook");
    if (!h.PostToolUse) errs.push("no PostToolUse hook");
    if (errs.length) { console.log(errs.join("; ")); process.exit(1); }
  ' 2>&1)" || bad "$PROBLEMS" "add the missing deny rules / hooks from templates/.claude/settings.json to .claude/settings.json (the permissions.deny list and the hooks block)"
else
  echo "⚠ harness: node not installed — .claude/settings.json was not checked."
fi

[ "$FAIL" = 0 ] && echo "harness: intact"
exit "$FAIL"
