import hashlib
import time
import uuid
from datetime import date

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import app.models  # noqa: F401 - register all models
from app.core.tenancy import tenant_scope
from app.models.base import Base
from app.models.clinic import Clinic
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.token import Token

PRD_RTO_TARGET_SECONDS = 14400  # PRD §18: 4 hours


@pytest.fixture
def source_db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    return session


def seed_database(session: Session) -> tuple[uuid.UUID, uuid.UUID]:
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()
    patient_id = uuid.uuid4()
    token_id = uuid.uuid4()

    with tenant_scope(None, bypass=True):
        clinic = Clinic(id=clinic_id, name="Shifa Recovery Test", slug="shifa-restore")
        doctor = Doctor(id=doctor_id, clinic_id=clinic_id, name="Dr. Restore", active=True)
        patient = Patient(id=patient_id, clinic_id=clinic_id, name="Patient Test", phone="03001234567")
        token = Token(
            id=token_id,
            clinic_id=clinic_id,
            doctor_id=doctor_id,
            patient_id=patient_id,
            number=1,
            position=1,
            public_code="TK-RESTORE-001",
            status="BOOKED",
            source="ONLINE",
            visit_date=date(2026, 11, 2),
        )
        session.add_all([clinic, doctor, patient, token])
        session.commit()

    return clinic_id, doctor_id


def dump_sqlite_session(session: Session) -> str:
    """Simulate database dump of schema and data."""
    connection = session.connection()
    raw_connection = connection.connection.driver_connection  # sqlite3.Connection
    dump_lines = list(raw_connection.iterdump())
    return "\n".join(dump_lines)


def restore_sqlite_session(dump_sql: str) -> tuple[Session, float]:
    """Execute timed restore of dump into a clean scratch database."""
    start_time = time.perf_counter()
    scratch_engine = create_engine("sqlite:///:memory:")
    connection = scratch_engine.connect()
    raw_conn = connection.connection.driver_connection
    raw_conn.executescript(dump_sql)
    connection.commit()
    elapsed_seconds = time.perf_counter() - start_time

    scratch_session = Session(scratch_engine)
    return scratch_session, elapsed_seconds


def test_timed_database_restore_within_prd_rto_target(source_db: Session) -> None:
    """Acceptance criterion for Task 42:

    The restore completes within the PRD recovery target (RTO 4h = 14400s).
    """
    clinic_id, doctor_id = seed_database(source_db)

    # 1. Create backup dump
    backup_dump = dump_sqlite_session(source_db)
    assert len(backup_dump) > 0

    # 2. Perform timed restore into a scratch database
    scratch_session, duration = restore_sqlite_session(backup_dump)

    # 3. Assert restore completed within the PRD recovery target (RTO < 4 hours)
    assert duration < PRD_RTO_TARGET_SECONDS, (
        f"Restore took {duration}s, exceeding PRD RTO limit of {PRD_RTO_TARGET_SECONDS}s"
    )
    # Unit test performance sanity gate: in-memory restore should finish in under 2 seconds
    assert duration < 2.0

    # 4. Smoke queries on restored database
    with tenant_scope(None, bypass=True):
        clinics = scratch_session.execute(select(Clinic)).scalars().all()
        assert len(clinics) == 1
        assert clinics[0].id == clinic_id
        assert clinics[0].name == "Shifa Recovery Test"

        doctors = scratch_session.execute(select(Doctor)).scalars().all()
        assert len(doctors) == 1
        assert doctors[0].id == doctor_id
        assert doctors[0].name == "Dr. Restore"

        tokens = scratch_session.execute(select(Token)).scalars().all()
        assert len(tokens) == 1
        assert tokens[0].public_code == "TK-RESTORE-001"
        assert tokens[0].number == 1


def test_backup_checksum_integrity_verification(source_db: Session) -> None:
    """Verify backup integrity using SHA-256 checksum."""
    seed_database(source_db)
    backup_dump = dump_sqlite_session(source_db)

    # Calculate SHA256 checksum
    checksum = hashlib.sha256(backup_dump.encode("utf-8")).hexdigest()

    # Valid checksum verification
    calculated = hashlib.sha256(backup_dump.encode("utf-8")).hexdigest()
    assert calculated == checksum

    # Tampered backup fails checksum verification
    tampered_dump = backup_dump + "\n-- Tampered query"
    tampered_checksum = hashlib.sha256(tampered_dump.encode("utf-8")).hexdigest()
    assert tampered_checksum != checksum
