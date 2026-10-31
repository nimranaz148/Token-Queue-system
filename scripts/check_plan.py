#!/usr/bin/env python3
"""Check context/build-plan.md and context/progress-tracker.md for the defects that waste a build.

  python3 scripts/check_plan.py [--context context]

Finds: duplicated tasks, tasks with no acceptance criteria, oversized tasks (too many criteria to verify
in one fast-tier cycle), a tracker that is too long or lacks its fixed status fields, and a tracker that
contradicts the build plan (a task ticked in one file and not the other, "Next" pointing at a finished
task, "Last completed" pointing at an unfinished one).

Exit 0: clean. Exit 1: one "✗ plan:" line and one "  next:" line per problem. Standard library only.
"""
import argparse
import difflib
import re
import sys
from pathlib import Path

MAX_CRITERIA = 6
MAX_TRACKER_LINES = 150
STATUS_FIELDS = ("Phase", "Last completed", "In progress", "Next", "Blockers")
TASK = re.compile(r"^- \[( |x|X)\] (\d{2,3}) (.*)$")
ID = re.compile(r"\b[A-Z]-\d{3}\b")


def parse_plan(text):
    tasks, cur = [], None
    for line in text.splitlines():
        m = TASK.match(line)
        if m:
            cur = {"done": m.group(1) != " ", "num": m.group(2), "text": m.group(3).strip(), "accept": 0}
            tasks.append(cur)
        elif cur is not None and line.startswith("  - Acceptance:"):
            cur["accept"] += 1
        elif line.startswith("#") or (line.strip() and not line.startswith(" ")):
            cur = None
    return tasks


def normalize(t):
    t = re.sub(r"\(.*?\)", " ", t.lower())
    return re.sub(r"[^a-z0-9 ]+", " ", t).split()


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--context", default="context")
    a = ap.parse_args()
    ctx = Path(a.context)
    plan_f, trk_f = ctx / "build-plan.md", ctx / "progress-tracker.md"
    bad = 0

    def problem(msg, nxt):
        nonlocal bad
        bad = 1
        print(f"✗ plan: {msg}")
        print(f"  next: {nxt}")

    if not plan_f.exists():
        problem(f"{plan_f} is missing", "run /bootstrap, or python3 scripts/context_from_prd.py docs/prd/PRD.md --out context")
        return 1
    tasks = parse_plan(plan_f.read_text(encoding="utf-8"))
    if not tasks:
        problem("build-plan.md has no numbered tasks (lines like '- [ ] 00 ...')", "regenerate it with context_from_prd.py or add tasks in that format")

    seen_ids = {}
    for t in tasks:
        for i in set(ID.findall(t["text"])):
            if i in seen_ids:
                problem(f"tasks {seen_ids[i]} and {t['num']} both implement {i}", f"keep one: delete or merge task {t['num']} into {seen_ids[i]} in build-plan.md")
            else:
                seen_ids[i] = t["num"]
    for x in range(len(tasks)):
        for y in range(x + 1, len(tasks)):
            tx, ty = tasks[x], tasks[y]
            if difflib.SequenceMatcher(None, normalize(tx["text"]), normalize(ty["text"])).ratio() >= 0.9:
                problem(f"tasks {tx['num']} and {ty['num']} are near-duplicates", f"keep one: delete or merge task {ty['num']} in build-plan.md")
    for t in tasks:
        if t["accept"] == 0:
            problem(f"task {t['num']} has no acceptance criteria", f"add at least one '  - Acceptance: <observable check>' line under task {t['num']}")
        elif t["accept"] > MAX_CRITERIA:
            problem(f"task {t['num']} has {t['accept']} acceptance criteria (max {MAX_CRITERIA}): too big for one fast-tier cycle", f"split task {t['num']} into smaller tasks, each with its own criteria")

    if trk_f.exists():
        trk = trk_f.read_text(encoding="utf-8")
        lines = trk.splitlines()
        if len(lines) > MAX_TRACKER_LINES:
            problem(f"progress-tracker.md is {len(lines)} lines (max {MAX_TRACKER_LINES})", "move history to context/progress-log.md and keep only the status block and checklists here")
        status = {}
        for f in STATUS_FIELDS:
            m = re.search(rf"^\*\*{re.escape(f)}:\*\*\s*(.*)$", trk, re.M)
            if not m:
                problem(f"progress-tracker.md has no '**{f}:**' status field", f"add the line '**{f}:** —' to the Current Status block")
            else:
                status[f] = m.group(1)
        ticks = {}
        for line in lines:
            m = TASK.match(line)
            if m:
                ticks[m.group(2)] = m.group(1) != " "
        by_num = {t["num"]: t for t in tasks}
        for num, done in ticks.items():
            if num in by_num and by_num[num]["done"] != done:
                problem(f"task {num} is {'done' if done else 'open'} in the tracker but {'done' if by_num[num]['done'] else 'open'} in the build plan", f"make both files agree on task {num} (tick or untick it in both)")
        for num in ticks:
            if num not in by_num:
                problem(f"tracker lists task {num}, which is not in the build plan", f"remove it from the tracker or add it to build-plan.md")
        nxt = re.match(r"\s*(\d{2,3})\b", status.get("Next", ""))
        if nxt and ticks.get(nxt.group(1)):
            problem(f"tracker says Next is task {nxt.group(1)}, but it is ticked done", "set Next to the first unticked task")
        last = re.match(r"\s*(\d{2,3})\b", status.get("Last completed", ""))
        if last and last.group(1) in ticks and not ticks[last.group(1)]:
            problem(f"tracker says task {last.group(1)} was completed, but it is not ticked", f"tick task {last.group(1)} in both files, or fix 'Last completed'")

    if not bad:
        print(f"plan: ok ({len(tasks)} tasks)")
    return bad


if __name__ == "__main__":
    sys.exit(main())
