#!/usr/bin/env python3
"""Validate a /review verdict before anything trusts it.

  python3 scripts/check_verdict.py verdict.json
  echo '{...}' | python3 scripts/check_verdict.py

Exit 0: valid. Exit 1: invalid, with one line per problem on stderr saying what to fix.
A verdict is machine-checkable on purpose: a free-text "mostly fine" cannot be branched on.
Standard library only.
"""
import json
import sys

VERDICTS = {"PASS", "FAIL"}
RISKS = {"low", "high"}
LAYERS = ("plan", "system", "production")
LAYER_STATES = {"PASS", "ISSUES"}
SEVERITIES = {"critical", "important", "minor"}


def validate(doc):
    if not isinstance(doc, dict):
        return ["the top level must be a JSON object, not " + type(doc).__name__]
    errs = []
    if doc.get("verdict") not in VERDICTS:
        errs.append('"verdict" must be exactly "PASS" or "FAIL"')
    if doc.get("risk") not in RISKS:
        errs.append('"risk" must be exactly "low" or "high"')
    layers, issues = doc.get("layers"), doc.get("issues")
    if not isinstance(layers, dict) or set(layers) != set(LAYERS) or any(v not in LAYER_STATES for v in layers.values()):
        errs.append('"layers" must have exactly plan, system and production, each "PASS" or "ISSUES"')
        layers = None
    if not isinstance(issues, list):
        errs.append('"issues" must be an array (empty when there are none)')
        issues = None
    if issues is not None:
        for i, it in enumerate(issues):
            ok = (
                isinstance(it, dict)
                and it.get("severity") in SEVERITIES
                and it.get("layer") in LAYERS
                and isinstance(it.get("text"), str)
                and it["text"].strip()
            )
            if not ok:
                errs.append(f"issues[{i}] needs severity (critical|important|minor), layer (plan|system|production) and non-empty text")
                issues = None
                break
    if errs:
        return errs
    blocking = [it for it in issues if it["severity"] in ("critical", "important")]
    if doc["verdict"] == "PASS" and blocking:
        errs.append('verdict is PASS but critical/important issues are listed: use "FAIL", or downgrade them to minor if they truly are')
    if doc["verdict"] == "FAIL" and not issues:
        errs.append('verdict is FAIL but "issues" is empty: list at least one issue')
    if any(it["severity"] == "critical" for it in issues) and doc["risk"] != "high":
        errs.append('a critical issue is listed but "risk" is not "high"')
    for layer in LAYERS:
        has = any(it["layer"] == layer for it in issues)
        if has != (layers[layer] == "ISSUES"):
            errs.append(f'layers.{layer} is "{layers[layer]}" but {"there are" if has else "there are no"} issues for it')
    return errs


def main(argv):
    try:
        raw = open(argv[1], "rb").read() if len(argv) > 1 else sys.stdin.buffer.read()
        raw = raw.decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as e:
        print(f"check_verdict: cannot read input: {e}", file=sys.stderr)
        return 1
    if not raw.strip():
        print("check_verdict: empty input. Reply with ONLY the verdict JSON object.", file=sys.stderr)
        return 1
    try:
        doc = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"check_verdict: not valid JSON ({e.msg}, line {e.lineno}). Reply with ONLY the verdict JSON object, no prose around it.", file=sys.stderr)
        return 1
    errs = validate(doc)
    for e in errs:
        print(f"check_verdict: {e}", file=sys.stderr)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
