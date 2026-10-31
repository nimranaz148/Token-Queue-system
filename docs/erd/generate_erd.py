#!/usr/bin/env python3
"""
Regenerates every docs/erd/*.md diagram from the LIVE database schema. The
migrations are the source of truth; this introspects the database they
produced, so a diagram can never describe a schema that does not exist.

Config: docs/erd/erd.config.json
  {
    "psql": ["docker", "compose", "exec", "-T", "db", "psql", "-U", "app", "-d", "app"],
    "cwd": "infra",
    "diagrams": [
      { "name": "Orders", "output": "orders.md", "template": "orders.template.md",
        "tables": { "Orders": ["orders", "order_lines"] } }
    ]
  }
"cwd" is relative to the repo root and optional. If "psql" is omitted,
`psql "$DATABASE_URL"` is used.

Each template holds the hand-written prose plus a {{DIAGRAM}} placeholder.
Usage:  python3 docs/erd/generate_erd.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ERD_DIR = Path(__file__).resolve().parent
REPO_ROOT = ERD_DIR.parents[1]
CONFIG = json.loads((ERD_DIR / "erd.config.json").read_text(encoding="utf-8"))

TYPE_MAP = {
    "character varying": "varchar",
    "timestamp with time zone": "timestamptz",
    "timestamp without time zone": "timestamp",
    "time without time zone": "time",
}


def psql_base() -> list[str]:
    if CONFIG.get("psql"):
        return list(CONFIG["psql"])
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit('Set DATABASE_URL or configure "psql" in erd.config.json.')
    return ["psql", url]


def run_sql(sql: str) -> list[list[str]]:
    cwd = REPO_ROOT / CONFIG["cwd"] if CONFIG.get("cwd") else REPO_ROOT
    try:
        result = subprocess.run(
            [*psql_base(), "-t", "-A", "-F|", "-c", sql],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        sys.exit(f"Could not query the database - is it running and migrated?\n{exc.stderr}")
    return [line.split("|") for line in result.stdout.splitlines() if line.strip()]


def in_list(tables: list[str]) -> str:
    return ",".join("'" + t.replace("'", "''") + "'" for t in tables)


def fetch_columns(tables: list[str]) -> list[list[str]]:
    return run_sql(f"""
        SELECT c.table_name, c.column_name, c.data_type,
               CASE WHEN pk.column_name IS NOT NULL THEN 'Y' ELSE '' END
        FROM information_schema.columns c
        LEFT JOIN (
          SELECT ku.table_name, ku.column_name
          FROM information_schema.table_constraints tc
          JOIN information_schema.key_column_usage ku
            ON tc.constraint_name = ku.constraint_name AND tc.table_schema = ku.table_schema
          WHERE tc.constraint_type = 'PRIMARY KEY' AND tc.table_schema = 'public'
        ) pk ON pk.table_name = c.table_name AND pk.column_name = c.column_name
        WHERE c.table_schema = 'public' AND c.table_name IN ({in_list(tables)})
        ORDER BY c.table_name, c.ordinal_position;""")


def fetch_foreign_keys(tables: list[str]) -> list[list[str]]:
    return run_sql(f"""
        SELECT tc.table_name, kcu.column_name, ccu.table_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public'
          AND tc.table_name IN ({in_list(tables)})
        ORDER BY tc.table_name, kcu.column_name;""")


def build(groups: dict[str, list[str]], columns: list[list[str]], fks: list[list[str]]) -> str:
    all_tables = [t for g in groups.values() for t in g]
    fk_cols = {(t, c) for t, c, _ in fks}
    by_table: dict[str, list[str]] = {t: [] for t in all_tables}
    for table, column, dtype, is_pk in columns:
        marker = " PK" if is_pk == "Y" else (" FK" if (table, column) in fk_cols else "")
        by_table[table].append(f"        {TYPE_MAP.get(dtype, dtype.replace(' ', '_'))} {column}{marker}")
    lines = ["erDiagram"]
    for group, tables in groups.items():
        lines.append(f"    %% {group}")
        for table in tables:
            lines.append(f"    {table} {{")
            lines.extend(by_table[table])
            lines.append("    }")
    lines.append("")
    seen: set[tuple[str, str, str]] = set()
    for from_table, from_column, to_table in fks:
        if (to_table, from_table, from_column) in seen:
            continue
        seen.add((to_table, from_table, from_column))
        lines.append(f'    {to_table} ||--o{{ {from_table} : "{from_column}"')
    return "\n".join(lines)


def main() -> None:
    for d in CONFIG["diagrams"]:
        tables = [t for g in d["tables"].values() for t in g]
        rendered = build(d["tables"], fetch_columns(tables), fetch_foreign_keys(tables))
        template = (ERD_DIR / d["template"]).read_text(encoding="utf-8")
        out = ERD_DIR / d["output"]
        out.write_text(template.replace("{{DIAGRAM}}", rendered), encoding="utf-8", newline="\n")
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
