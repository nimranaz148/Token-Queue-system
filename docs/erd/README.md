# Database Documentation (`docs/erd/`)

Diagrams are **generated** from the live database, never hand-drawn.

- `<context>.md` — generated ERD. Do not edit.
- `<context>.template.md` — hand-written prose around the diagram. Edit this.
- `erd.config.json` — which tables belong to which diagram, and how to reach the database.
- `generate_erd.py` — regenerates every diagram.

## Regenerating

1. Start the database and apply pending migrations.
2. `python3 docs/erd/generate_erd.py`
3. Review the diff and commit it with the migration that caused it.

Run this whenever a migration adds, removes or renames a table or column in a
documented bounded context. To document a new context, add an entry to
`erd.config.json` and a `<context>.template.md` containing `{{DIAGRAM}}`.
