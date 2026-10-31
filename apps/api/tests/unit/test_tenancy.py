import uuid
from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import app.models  # noqa: F401 - ensure all models are registered
from app.core.errors import AppException
from app.core.tenancy import tenant_scope
from app.models.base import Base
from app.models.clinic import Clinic
from app.models.patient import Patient


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


@pytest.fixture
def seeded_clinics(db_session: Session) -> tuple[uuid.UUID, uuid.UUID]:
    """Seed two distinct clinics (Clinic A and Clinic B) under platform bypass."""
    clinic_a_id = uuid.uuid4()
    clinic_b_id = uuid.uuid4()

    with tenant_scope(None, bypass=True):
        clinic_a = Clinic(id=clinic_a_id, name="Clinic Alpha", slug="clinic-alpha")
        clinic_b = Clinic(id=clinic_b_id, name="Clinic Beta", slug="clinic-beta")
        db_session.add_all([clinic_a, clinic_b])

        patient_a = Patient(
            id=uuid.uuid4(),
            clinic_id=clinic_a_id,
            name="Patient Alpha",
            phone="03001111111",
        )
        patient_b = Patient(
            id=uuid.uuid4(),
            clinic_id=clinic_b_id,
            name="Patient Beta",
            phone="03002222222",
        )
        db_session.add_all([patient_a, patient_b])
        db_session.commit()

    return clinic_a_id, clinic_b_id


def test_deny_by_default_returns_zero_rows(
    db_session: Session, seeded_clinics: tuple[uuid.UUID, uuid.UUID]
) -> None:
    """Without tenant context, querying tenant-scoped entities returns zero rows."""
    with tenant_scope(None, bypass=False):
        patients = db_session.execute(select(Patient)).scalars().all()
        assert len(patients) == 0

        clinics = db_session.execute(select(Clinic)).scalars().all()
        assert len(clinics) == 0


def test_tenant_a_cannot_read_tenant_b_rows(
    db_session: Session, seeded_clinics: tuple[uuid.UUID, uuid.UUID]
) -> None:
    """Tenant A can only read Tenant A rows; Tenant B rows are invisible."""
    clinic_a_id, clinic_b_id = seeded_clinics

    # In Clinic A scope
    with tenant_scope(clinic_a_id):
        patients_a = db_session.execute(select(Patient)).scalars().all()
        assert len(patients_a) == 1
        assert patients_a[0].clinic_id == clinic_a_id
        assert patients_a[0].name == "Patient Alpha"

        # Explicit query for Tenant B's patient returns None (denied/filtered)
        patient_b = (
            db_session.execute(select(Patient).where(Patient.clinic_id == clinic_b_id))
            .scalars()
            .first()
        )
        assert patient_b is None

    # In Clinic B scope
    with tenant_scope(clinic_b_id):
        patients_b = db_session.execute(select(Patient)).scalars().all()
        assert len(patients_b) == 1
        assert patients_b[0].clinic_id == clinic_b_id
        assert patients_b[0].name == "Patient Beta"


def test_tenant_a_cannot_write_tenant_b_rows(
    db_session: Session, seeded_clinics: tuple[uuid.UUID, uuid.UUID]
) -> None:
    """Tenant A cannot persist a record belonging to Tenant B."""
    clinic_a_id, clinic_b_id = seeded_clinics

    with tenant_scope(clinic_a_id):
        malicious_patient = Patient(
            id=uuid.uuid4(),
            clinic_id=clinic_b_id,  # Trying to insert into Clinic B
            name="Malicious Patient",
            phone="03009999999",
        )
        db_session.add(malicious_patient)
        with pytest.raises(AppException) as exc_info:
            db_session.flush()

        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "CROSS_TENANT_ACCESS"


def test_tenant_a_cannot_modify_tenant_b_rows(
    db_session: Session, seeded_clinics: tuple[uuid.UUID, uuid.UUID]
) -> None:
    """Tenant A cannot modify a record belonging to Tenant B."""
    clinic_a_id, clinic_b_id = seeded_clinics

    with tenant_scope(None, bypass=True):
        patient_b = (
            db_session.execute(select(Patient).where(Patient.clinic_id == clinic_b_id))
            .scalars()
            .one()
        )

    with tenant_scope(clinic_a_id):
        patient_b.name = "Tampered Name"
        with pytest.raises(AppException) as exc_info:
            db_session.flush()

        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "CROSS_TENANT_ACCESS"


def test_insert_without_tenant_context_is_denied(db_session: Session) -> None:
    """Attempting to persist a tenant entity with no tenant context raises 403."""
    with tenant_scope(None, bypass=False):
        orphan_patient = Patient(
            id=uuid.uuid4(),
            clinic_id=uuid.uuid4(),
            name="Orphan Patient",
            phone="03000000000",
        )
        db_session.add(orphan_patient)
        with pytest.raises(AppException) as exc_info:
            db_session.flush()

        assert exc_info.value.status_code == 403
        assert exc_info.value.code == "TENANT_REQUIRED"


def test_auto_assign_clinic_id_on_insert(
    db_session: Session, seeded_clinics: tuple[uuid.UUID, uuid.UUID]
) -> None:
    """When inserting with clinic_id=None under active scope, clinic_id is assigned."""
    clinic_a_id, _ = seeded_clinics

    with tenant_scope(clinic_a_id):
        new_patient = Patient(
            id=uuid.uuid4(),
            clinic_id=None,  # Not explicitly set
            name="Auto Scoped Patient",
            phone="03003333333",
        )
        db_session.add(new_patient)
        db_session.flush()
        assert new_patient.clinic_id == clinic_a_id


def test_platform_admin_bypasses_scope(
    db_session: Session, seeded_clinics: tuple[uuid.UUID, uuid.UUID]
) -> None:
    """Platform admin / bypass mode can query across all tenants."""
    with tenant_scope(None, bypass=True):
        all_patients = db_session.execute(select(Patient)).scalars().all()
        assert len(all_patients) == 2

        all_clinics = db_session.execute(select(Clinic)).scalars().all()
        assert len(all_clinics) == 2


def test_clinic_model_scoping(
    db_session: Session, seeded_clinics: tuple[uuid.UUID, uuid.UUID]
) -> None:
    """Clinic model itself is scoped to only the current tenant's clinic."""
    clinic_a_id, clinic_b_id = seeded_clinics

    with tenant_scope(clinic_a_id):
        clinics = db_session.execute(select(Clinic)).scalars().all()
        assert len(clinics) == 1
        assert clinics[0].id == clinic_a_id

    with tenant_scope(clinic_b_id):
        clinics = db_session.execute(select(Clinic)).scalars().all()
        assert len(clinics) == 1
        assert clinics[0].id == clinic_b_id
