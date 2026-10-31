import uuid
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import app.models  # noqa: F401 - ensure all models are registered
from app.core.masking import hash_ip, mask_email, mask_name, mask_phone, mask_sensitive_data
from app.core.tenancy import tenant_scope
from app.models.audit import AuditLog
from app.models.base import Base
from app.schemas.audit import AuditAction
from app.services.audit import AuditService


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Provide an in-memory SQLite database session with all models created."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    try:
        yield session
    finally:
        session.close()


# 1. Test Sensitive Field Masking


def test_mask_phone() -> None:
    assert mask_phone("03001234567") == "0300****567"
    assert mask_phone("+923001234567") == "+923******567"
    assert mask_phone("12345") == "***"
    assert mask_phone(None) is None


def test_mask_name() -> None:
    assert mask_name("Muhammad Ali") == "M*** A***"
    assert mask_name("John") == "J***"
    assert mask_name(None) is None


def test_mask_email() -> None:
    assert mask_email("doctor@example.com") == "d***@example.com"
    assert mask_email("a@b.com") == "***@b.com"
    assert mask_email(None) is None


def test_hash_ip() -> None:
    ip1 = "192.168.1.1"
    ip2 = "192.168.1.2"
    h1 = hash_ip(ip1)
    h2 = hash_ip(ip2)
    assert h1 is not None and len(h1) == 16
    assert h1 != ip1  # Raw IP is not stored
    assert h1 != h2  # Different IPs produce different hashes
    assert hash_ip(None) is None


def test_mask_sensitive_data_dictionary() -> None:
    raw_payload = {
        "name": "Jane Doe",
        "phone": "03009876543",
        "email": "jane@example.com",
        "password": "supersecretpassword",
        "token": "bearer-xyz-123",
        "notes": "Patient reports severe chest pain and breathlessness.",
        "cnic": "42101-1234567-1",
        "number": 42,
        "status": "arrived",
    }

    masked = mask_sensitive_data(raw_payload)
    assert masked is not None
    assert masked["name"] == "J*** D***"
    assert masked["phone"] == "0300****543"
    assert masked["email"] == "j***@example.com"
    assert masked["password"] == "[REDACTED]"
    assert masked["token"] == "[REDACTED]"
    assert masked["notes"] == "[REDACTED_HEALTH_DATA]"
    assert masked["cnic"] == "[REDACTED_CNIC]"
    # Non-sensitive fields preserved as-is
    assert masked["number"] == 42
    assert masked["status"] == "arrived"


# 2. Acceptance Test: Every Audited Action in PRD §14.1 Writes Exactly One Audit Row


@pytest.mark.parametrize("action", list(AuditAction))
def test_each_audited_action_writes_audit_row(
    db_session: Session,
    action: AuditAction,
) -> None:
    """Acceptance criterion: Each audited action in PRD §14.1 writes exactly one audit row."""
    clinic_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    entity_id = uuid.uuid4()

    with tenant_scope(clinic_id):
        # Count existing rows before
        count_before = (
            db_session.execute(select(AuditLog).where(AuditLog.action == action.value))
            .scalars()
            .all()
        )

        entry = AuditService.record_audit(
            session=db_session,
            action=action,
            entity="test_entity",
            entity_id=entity_id,
            actor_type="staff",
            actor_id=actor_id,
            clinic_id=clinic_id,
            before={"status": "old", "phone": "03001111111"},
            after={"status": "new", "phone": "03002222222", "notes": "Private medical note"},
            request_id="req-12345",
            client_ip="10.0.0.1",
        )
        db_session.flush()

        assert entry.id is not None
        assert entry.action == action.value
        assert entry.clinic_id == clinic_id
        assert entry.actor_id == actor_id
        assert entry.entity_id == entity_id
        assert entry.request_id == "req-12345"
        assert entry.ip_hash is not None
        assert entry.at is not None

        # Verify sensitive masking in the stored row
        assert entry.before is not None
        assert entry.before["phone"] == "0300****111"
        assert entry.after is not None
        assert entry.after["phone"] == "0300****222"
        assert entry.after["notes"] == "[REDACTED_HEALTH_DATA]"

        # Exactly one new row added for this action
        count_after = (
            db_session.execute(select(AuditLog).where(AuditLog.action == action.value))
            .scalars()
            .all()
        )
        assert len(count_after) == len(count_before) + 1


# 3. Test Audit Log Scoping Isolation


def test_audit_log_tenant_isolation(db_session: Session) -> None:
    """Audit logs are scoped to the clinic: Tenant A cannot see Tenant B's audit trail."""
    clinic_a = uuid.uuid4()
    clinic_b = uuid.uuid4()

    # Record log for Clinic A
    with tenant_scope(clinic_a):
        AuditService.record_audit(
            session=db_session,
            action=AuditAction.TOKEN_CREATE,
            entity="token",
            clinic_id=clinic_a,
            after={"number": 1},
        )
        db_session.flush()

    # Record log for Clinic B
    with tenant_scope(clinic_b):
        AuditService.record_audit(
            session=db_session,
            action=AuditAction.TOKEN_CREATE,
            entity="token",
            clinic_id=clinic_b,
            after={"number": 2},
        )
        db_session.flush()

    # Clinic A sees only Clinic A audit logs
    with tenant_scope(clinic_a):
        logs_a = db_session.execute(select(AuditLog)).scalars().all()
        assert len(logs_a) == 1
        assert logs_a[0].clinic_id == clinic_a

    # Clinic B sees only Clinic B audit logs
    with tenant_scope(clinic_b):
        logs_b = db_session.execute(select(AuditLog)).scalars().all()
        assert len(logs_b) == 1
        assert logs_b[0].clinic_id == clinic_b

    # Platform admin in bypass mode sees all audit logs
    with tenant_scope(None, bypass=True):
        all_logs = db_session.execute(select(AuditLog)).scalars().all()
        assert len(all_logs) == 2
