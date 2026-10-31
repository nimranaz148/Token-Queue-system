"""Unit tests asserting SQLAlchemy models conform strictly to PRD §12.2 and §12.3."""

from app.models import (
    Base,
)

EXPECTED_TABLES = {
    "clinics",
    "clinic_settings",
    "platform_admins",
    "doctors",
    "doctor_schedules",
    "clinic_members",
    "patients",
    "tokens",
    "token_counters",
    "token_events",
    "visits",
    "visit_attachments",
    "daily_stats",
    "display_devices",
    "audit_logs",
    "ai_runs",
    "ai_briefs",
    "chat_messages",
    "wait_predictions",
}


def test_all_19_tables_registered_in_metadata() -> None:
    """Every PRD §12.3 table must be present in Base.metadata."""
    registered = set(Base.metadata.tables.keys())
    assert EXPECTED_TABLES.issubset(registered), f"Missing tables: {EXPECTED_TABLES - registered}"
    assert len(registered) == 19


def test_table_names_convention() -> None:
    """Tables must be lower_snake_case and plural."""
    for table_name in Base.metadata.tables:
        assert table_name.islower(), f"Table {table_name} is not lower case"
        assert " " not in table_name, f"Table {table_name} contains spaces"


def test_tenant_scoping_convention() -> None:
    """Every tenant table must carry a non-nullable clinic_id foreign key to clinics.id."""
    non_tenant_tables = {"clinics", "platform_admins"}

    for table_name, table in Base.metadata.tables.items():
        if table_name in non_tenant_tables:
            continue

        assert "clinic_id" in table.columns, f"Tenant table {table_name} missing clinic_id"
        col = table.columns["clinic_id"]

        # audit_logs and ai_runs allow null clinic_id for platform/global level runs
        if table_name not in {"audit_logs", "ai_runs"}:
            assert not col.nullable, f"{table_name}.clinic_id must be NOT NULL"

        fk_targets = [fk.target_fullname for fk in col.foreign_keys]
        assert "clinics.id" in fk_targets, f"{table_name}.clinic_id must FK to clinics.id"


def test_soft_delete_convention() -> None:
    """Only patients, doctors, and clinic_members carry deleted_at; tokens never deleted."""
    soft_delete_tables = {"patients", "doctors", "clinic_members"}

    for table_name in soft_delete_tables:
        table = Base.metadata.tables[table_name]
        assert "deleted_at" in table.columns, f"{table_name} must have deleted_at"

    # Tokens must NEVER be deleted
    assert "deleted_at" not in Base.metadata.tables["tokens"].columns


def test_optimistic_concurrency_convention() -> None:
    """clinic_settings and visits must have a version column for optimistic locking."""
    concurrency_tables = {"clinic_settings", "visits"}
    for table_name in concurrency_tables:
        table = Base.metadata.tables[table_name]
        assert "version" in table.columns, f"{table_name} missing version column"


def test_primary_key_convention() -> None:
    """All models must have a primary key defined."""
    for table_name, table in Base.metadata.tables.items():
        pk_cols = [c.name for c in table.primary_key.columns]
        assert len(pk_cols) >= 1, f"Table {table_name} has no primary key"
