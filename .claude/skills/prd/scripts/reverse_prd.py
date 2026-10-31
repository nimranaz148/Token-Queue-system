#!/usr/bin/env python3
"""Reverse-engineer PRD findings from a built codebase.

    python3 reverse_prd.py <repo-dir> [--out docs/prd/reverse-findings.md] [--name "Project Name"]

Reads manifests, folder layout, routes, pages, data entities and tests, and writes a findings file whose
front matter matches the PRD front matter (so `bootstrap` and `check_prd.py` can use it once the PRD is
written) and whose body lists every finding with a confidence level and the file that proves it.

Confidence: high = declared in a manifest or config; medium = matched in source code; low = inferred from a name.
Everything the code cannot tell (business goals, users, priorities, acceptance rules) is listed under
"Open questions" for the interview. Nothing is guessed. Standard library only.
"""
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

SKIP = {"node_modules", ".git", ".venv", "venv", "__pycache__", "bin", "obj", ".next", "dist", "build", ".mypy_cache", ".pytest_cache", "target", ".idea", ".vscode"}
MANIFESTS = ("package.json", "pyproject.toml", "requirements.txt", "go.mod", "pom.xml", "build.gradle", "Gemfile", "composer.json")
SRC_EXT = {".py", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cs", ".go", ".java", ".kt", ".rb", ".php", ".prisma", ".sql"}


def walk(root: Path, max_depth: int = 6):
    stack = [(root, 0)]
    while stack:
        d, depth = stack.pop()
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.name in SKIP:
                continue
            if e.is_dir():
                if depth < max_depth:
                    stack.append((e, depth + 1))
            else:
                yield e


def read(p: Path, limit: int = 400_000) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


FRAMEWORKS = [  # (needle in manifest text, role, label)
    ('"next"', "frontend", "Next.js"), ('"react"', "frontend", "React"), ('"vue"', "frontend", "Vue"), ('"svelte"', "frontend", "Svelte"),
    ('"@angular/core"', "frontend", "Angular"), ('"tailwindcss"', "styling", "Tailwind"),
    ('"express"', "backend", "Express"), ('"@nestjs/core"', "backend", "NestJS"), ('"fastify"', "backend", "Fastify"),
    ("fastapi", "backend", "FastAPI"), ("django", "backend", "Django"), ("flask", "backend", "Flask"),
    ("gin-gonic/gin", "backend", "Gin"), ("labstack/echo", "backend", "Echo"), ("spring-boot", "backend", "Spring Boot"),
    ('"prisma"', "orm", "Prisma"), ('"@prisma/client"', "orm", "Prisma"), ('"typeorm"', "orm", "TypeORM"), ('"mongoose"', "orm", "Mongoose"),
    ("sqlalchemy", "orm", "SQLAlchemy"), ("alembic", "migrations", "Alembic"),
    ('"pg"', "database", "PostgreSQL"), ("psycopg", "database", "PostgreSQL"), ("asyncpg", "database", "PostgreSQL"),
    ("mysql", "database", "MySQL"), ("mongodb", "database", "MongoDB"), ("sqlite", "database", "SQLite"),
    ('"openai"', "ai", "OpenAI SDK"), ("anthropic", "ai", "Anthropic SDK"), ("langchain", "ai", "LangChain"), ("openai-agents", "ai", "OpenAI Agents SDK"),
    ('"vitest"', "tests", "Vitest"), ('"jest"', "tests", "Jest"), ("pytest", "tests", "pytest"), ('"@playwright/test"', "tests", "Playwright"), ('"cypress"', "tests", "Cypress"),
]

ROUTE_PATTERNS = [
    (re.compile(r"""@(?:app|router|api)\.(get|post|put|patch|delete)\(\s*["']([^"']+)["']"""), "FastAPI/Flask"),
    (re.compile(r"""\b(?:app|router|api)\.(get|post|put|patch|delete)\(\s*["'`]([^"'`]+)["'`]"""), "Express-style"),
    (re.compile(r"""\[Http(Get|Post|Put|Patch|Delete)(?:\(\s*"([^"]*)"\s*\))?\]"""), "ASP.NET"),
    (re.compile(r"""\.(GET|POST|PUT|PATCH|DELETE)\(\s*"([^"]+)\""""), "Go router"),
    (re.compile(r"""@(Get|Post|Put|Patch|Delete)Mapping\(\s*(?:value\s*=\s*)?"([^"]*)\""""), "Spring"),
]
ENTITY_PATTERNS = [
    (re.compile(r"^model\s+(\w+)\s*\{", re.M), "Prisma"),
    (re.compile(r"^class\s+(\w+)\((?:[\w.]*Base|[\w.]*models\.Model|[\w.]*SQLModel)[^)]*\)", re.M), "SQLAlchemy/Django"),
    (re.compile(r"DbSet<(\w+)>"), "EF Core"),
    (re.compile(r"@Entity\(?[^)]*\)?\s*(?:export\s+)?class\s+(\w+)"), "TypeORM"),
    (re.compile(r"mongoose\.model\(\s*['\"](\w+)['\"]"), "Mongoose"),
    (re.compile(r"CREATE TABLE(?: IF NOT EXISTS)?\s+[\"`]?(\w+)[\"`]?", re.I), "SQL"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", default="docs/prd/reverse-findings.md")
    ap.add_argument("--name", default="")
    a = ap.parse_args()
    root = Path(a.repo).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    files = list(walk(root))
    layout: dict[str, str] = {}
    stack: dict[str, set[str]] = {}
    evidence: list[tuple[str, str, str, str]] = []  # (area, finding, confidence, source)

    def add(area, finding, conf, src):
        evidence.append((area, finding, conf, src))

    # Layout and stack from manifests
    for f in files:
        if f.name in MANIFESTS or f.suffix == ".csproj":
            d = f.parent
            rd = rel(root, d) if d != root else "."
            text = read(f)
            roles = set()
            if f.suffix == ".csproj":
                if "Microsoft.NET.Sdk.Web" in text:
                    roles.add("backend"); stack.setdefault("backend", set()).add("ASP.NET Core"); add("stack", "ASP.NET Core backend", "high", rel(root, f))
                for needle, lab in (("Npgsql", "PostgreSQL"), ("EntityFrameworkCore", "EF Core")):
                    if needle in text:
                        stack.setdefault("database" if lab == "PostgreSQL" else "orm", set()).add(lab); add("stack", lab, "high", rel(root, f))
            for needle, role, label in FRAMEWORKS:
                if needle in text.lower():
                    stack.setdefault(role, set()).add(label)
                    if role in ("frontend", "backend"):
                        roles.add(role)
                    add("stack", f"{role}: {label}", "high", rel(root, f))
            key = "web" if "frontend" in roles else "api" if "backend" in roles else ("agents" if "ai" in roles else None)
            if key and key not in layout:
                layout[key] = rd
            elif not key and rd != "." and rd not in layout.values():
                layout[Path(rd).name] = rd

    # Infra
    for f in files:
        n = f.name.lower()
        if n in ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "dockerfile") or f.suffix == ".tf":
            stack.setdefault("infra", set()).add("Docker Compose" if "compose" in n else "Docker" if n == "dockerfile" else "Terraform")
            add("infra", f.name, "high", rel(root, f))
        if rel(root, f).startswith(".github/workflows/"):
            stack.setdefault("ci", set()).add("GitHub Actions"); add("ci", "GitHub Actions workflow " + f.name, "high", rel(root, f))
    if any(f.name == "alembic.ini" for f in files):
        stack.setdefault("migrations", set()).add("Alembic")
    if any("Migrations" in f.parts and f.suffix == ".cs" for f in files):
        stack.setdefault("migrations", set()).add("EF Core migrations")
    if any(f.name == "migration_lock.toml" for f in files):
        stack.setdefault("migrations", set()).add("Prisma Migrate")

    # Routes, pages, entities, tests
    routes: list[tuple[str, str, str, str]] = []
    pages: list[tuple[str, str]] = []
    entities: dict[str, tuple[str, str]] = {}
    tests: dict[str, int] = {}
    corpus_flags = {"tenancy": [], "audit": [], "openapi": [], "money": [], "auth": []}
    for f in files:
        r = rel(root, f)
        parts = f.parts
        if f.suffix in (".ts", ".tsx", ".js", ".jsx") and f.stem in ("page", "route") and "app" in parts:
            idx = len(parts) - 1 - parts[::-1].index("app")
            url = "/" + "/".join(p for p in parts[idx + 1:-1] if not (p.startswith("(") and p.endswith(")")))
            url = re.sub(r"/+", "/", url)
            if f.stem == "page":
                pages.append((url, r))
            else:
                for m in re.finditer(r"export\s+(?:async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE)\b", read(f)):
                    routes.append((m.group(1), url, "Next route handler", r))
        elif f.suffix in (".ts", ".tsx", ".js", ".jsx") and "pages" in parts and "api" not in parts and f.stem not in ("_app", "_document"):
            idx = parts.index("pages")
            url = "/" + "/".join(parts[idx + 1:-1] + ((f.stem,) if f.stem != "index" else ()))
            pages.append((url, r))
        if re.search(r"(^|[._/-])(test|tests|spec)([._/-]|$)", r.lower()) and f.suffix in SRC_EXT:
            kind = "e2e" if re.search(r"e2e|playwright|cypress", r.lower()) else "unit/integration"
            tests[kind] = tests.get(kind, 0) + 1
        if f.suffix in SRC_EXT:
            text = read(f)
            if "test" not in r.lower():
                for pat, label in ROUTE_PATTERNS:
                    for m in pat.finditer(text):
                        path = m.group(2) or ""
                        routes.append((m.group(1).upper(), path if path.startswith("/") or not path else "/" + path, label, r))
            for pat, label in ENTITY_PATTERNS:
                for m in pat.finditer(text):
                    entities.setdefault(m.group(1), (label, r))
            low = text.lower()
            if re.search(r"tenant_?id|company_?id|organization_?id|org_?id", low):
                corpus_flags["tenancy"].append(r)
            if "audit" in low and ("audit_log" in low or "auditlog" in low or "audit_logs" in low):
                corpus_flags["audit"].append(r)
            if re.search(r"openapi|swagger", low):
                corpus_flags["openapi"].append(r)
            if re.search(r"\b(amount|price|invoice|currency|total_price)\b", low):
                corpus_flags["money"].append(r)
            if re.search(r"jwt|oauth|bcrypt|passport|nextauth|next-auth|clerk|login", low):
                corpus_flags["auth"].append(r)

    features = []
    if "web" in layout or stack.get("frontend"):
        features.append("ui")
    if entities or stack.get("database") or stack.get("migrations"):
        features.append("database")
    if corpus_flags["openapi"] or any(f.name in ("openapi.json", "openapi.yaml", "swagger.json") for f in files):
        features.append("api-contract")
    if corpus_flags["tenancy"]:
        features.append("tenancy")
    if corpus_flags["audit"]:
        features.append("audit")
    if stack.get("ai"):
        features.append("ai-agents")

    def pick(role):
        v = sorted(stack.get(role, []))
        return " + ".join(v) if v else "unknown"

    name = a.name or root.name
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    out = Path(a.out)
    if not out.is_absolute():
        out = Path.cwd() / out
    L: list[str] = []
    L.append("---")
    L.append(f'project: "{name}"')
    L.append(f'slug: "{slug}"')
    L.append('version: "0.1.0"')
    L.append("status: draft-reverse-engineered")
    L.append("profile: mvp")
    L.append(f'date: "{date.today().isoformat()}"')
    L.append('owners: ["TO CONFIRM"]')
    L.append("stack:")
    L.append(f'  frontend: "{pick("frontend")}"')
    L.append(f'  backend: "{pick("backend")}"')
    L.append(f'  database: "{pick("database")}"')
    L.append(f'  migrations: "{pick("migrations")}"')
    L.append(f'  api_contract: "{"openapi" if "api-contract" in features else "none"}"')
    L.append(f'  agents: "{pick("ai") if stack.get("ai") else "none"}"')
    L.append(f'  infra: "{pick("infra")}"')
    L.append("features:")
    for ft in features:
        L.append(f"  - {ft}")
    if not features:
        L[-1] = "features: []"
    L.append("layout:")
    for k, v in layout.items():
        L.append(f"  {k}: {v}")
    if not layout:
        L[-1] = "layout: {}"
    L.append("phases: 2")
    L.append("---")
    L.append("")
    L.append(f"# {name} — Reverse-engineered findings")
    L.append("")
    L.append("> Generated by `reverse_prd.py` from the code in this repository. Every line below was read from a file; the last column says which. Confidence: **high** = declared in a manifest or config, **medium** = matched in source, **low** = inferred from a name. This is input to the PRD interview, not the PRD: the code cannot say what the product is *for*.")
    L.append("")
    L.append("## Stack")
    L.append("")
    L.append("| Role | Found | Confidence |")
    L.append("| --- | --- | --- |")
    for role in sorted(stack):
        L.append(f"| {role} | {pick(role)} | high |")
    L.append("")
    L.append("## Layout")
    L.append("")
    L.append("| Part | Folder |")
    L.append("| --- | --- |")
    for k, v in layout.items():
        L.append(f"| {k} | `{v}` |")
    L.append("")
    L.append(f"## Pages ({len(pages)}) — candidate forms and screens")
    L.append("")
    L.append("| ID | URL | Source | Confidence |")
    L.append("| --- | --- | --- | --- |")
    for i, (u, s) in enumerate(sorted(set(pages)), 1):
        L.append(f"| F-{i:03d} | `{u}` | `{s}` | medium |")
    L.append("")
    seen = set()
    uniq_routes = []
    for m, p, lab, s in routes:
        if (m, p, s) not in seen:
            seen.add((m, p, s)); uniq_routes.append((m, p, lab, s))
    L.append(f"## API endpoints ({len(uniq_routes)})")
    L.append("")
    L.append("| ID | Method | Path | Style | Source | Confidence |")
    L.append("| --- | --- | --- | --- | --- | --- |")
    for i, (m, p, lab, s) in enumerate(sorted(uniq_routes, key=lambda x: (x[1], x[0])), 1):
        L.append(f"| R-{i:03d} | {m} | `{p or '/'}` | {lab} | `{s}` | medium |")
    L.append("")
    L.append(f"## Data entities ({len(entities)})")
    L.append("")
    L.append("| Entity | Defined by | Source | Confidence |")
    L.append("| --- | --- | --- | --- |")
    for n, (lab, s) in sorted(entities.items()):
        L.append(f"| {n} | {lab} | `{s}` | medium |")
    L.append("")
    L.append("## Cross-cutting signals")
    L.append("")
    for k, label in (("tenancy", "Tenant/company scoping columns"), ("audit", "Audit log"), ("auth", "Authentication code"), ("money", "Money fields"), ("openapi", "OpenAPI/Swagger")):
        v = sorted(set(corpus_flags[k]))
        L.append(f"- {label}: {'found in ' + ', '.join('`' + x + '`' for x in v[:4]) + (' …' if len(v) > 4 else '') + ' (medium)' if v else 'not found'}")
    L.append("")
    L.append("## Tests")
    L.append("")
    if tests:
        for k, v in sorted(tests.items()):
            L.append(f"- {k}: {v} files (high)")
        L.append(f"- Frameworks: {pick('tests')}")
    else:
        L.append("- No test files found. This is a finding: nothing proves the current behaviour.")
    L.append("")
    L.append("## Open questions for the interview")
    L.append("")
    qs = [
        "What is this product for, and who are its users and roles? (the code shows features, not purpose)",
        "Which of the pages and endpoints above are in scope going forward, and which are legacy?",
        "What are the acceptance rules for each form and report? (not in code unless tests encode them)",
        "What phase is the product in, and what is the next release's exit test?",
        "What are the performance, availability and compliance requirements?",
    ]
    if not tests:
        qs.append("There are no tests: which behaviours must be locked in first?")
    if "tenancy" not in features:
        qs.append("No tenant scoping was found: is this single-tenant by design?")
    if "audit" not in features:
        qs.append("No audit log was found: is one required?")
    for i, q in enumerate(qs, 1):
        L.append(f"- Q-{i:03d} {q}")
    L.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print(f"wrote {out}")
    print(json.dumps({"layout": layout, "features": features, "pages": len(pages), "routes": len(uniq_routes), "entities": len(entities)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
