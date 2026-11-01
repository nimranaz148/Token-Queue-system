import uuid
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppException
from app.core.tenancy import async_tenant_scope
from app.models.clinic import Clinic, ClinicSettings
from app.models.doctor import Doctor
from app.models.member import ClinicMember
from app.models.token import Token
from app.schemas.audit import AuditAction
from app.schemas.auth import Role
from app.schemas.clinic import ClinicCreate
from app.services.audit import AuditService


class ClinicService:
    """Domain service managing clinic onboarding, status lifecycles, and configuration."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_clinic(
        self,
        data: ClinicCreate,
        created_by: uuid.UUID | None = None,
        ip_address: str | None = None,
    ) -> Clinic:
        """Create a new clinic tenant in 'trial' state with default operational settings."""
        # Check slug uniqueness
        existing_stmt = select(Clinic).where(Clinic.slug == data.slug)
        existing_res = await self.session.execute(existing_stmt)
        if existing_res.scalar_one_or_none():
            raise AppException(
                status_code=409,
                code="SLUG_EXISTS",
                detail=f"Clinic with slug '{data.slug}' already exists",
            )

        now = datetime.now(UTC)
        clinic = Clinic(
            id=uuid.uuid4(),
            name=data.name,
            slug=data.slug,
            time_zone=data.time_zone or "Asia/Karachi",
            address=data.address,
            phone=data.phone,
            status=data.status or "trial",
            created_at=now,
            updated_at=now,
        )
        self.session.add(clinic)
        await self.session.flush()

        # Initialize default clinic settings
        settings = ClinicSettings(
            clinic_id=clinic.id,
            online_booking_enabled=True,
            daily_online_limit=50,
            advance_days=1,
            default_consult_minutes=10,
            call_only_arrived=False,
            language_default="en",
            share_advice_with_patient=False,
            ai_notes_enabled=False,
        )
        self.session.add(settings)
        await self.session.flush()

        # Provision clinic owner in clinic_members (PRD §5.3 F-013)
        owner_member = ClinicMember(
            id=uuid.uuid4(),
            clinic_id=clinic.id,
            user_id=uuid.uuid4(),
            name=data.owner_name,
            email=str(data.owner_email),
            phone=data.owner_phone,
            role=Role.OWNER,
            active=True,
            created_at=now,
            updated_at=now,
        )
        self.session.add(owner_member)
        await self.session.flush()

        # Record immutable audit logs (PRD §14.1)
        AuditService.record_audit(
            session=self.session,
            action=AuditAction.CLINIC_CREATE,
            entity="clinic",
            entity_id=clinic.id,
            actor_type="platform_admin" if created_by else "system",
            actor_id=created_by,
            clinic_id=clinic.id,
            after={"slug": clinic.slug, "name": clinic.name, "status": clinic.status},
            client_ip=ip_address,
        )

        AuditService.record_audit(
            session=self.session,
            action=AuditAction.MEMBER_INVITE,
            entity="member",
            entity_id=owner_member.id,
            actor_type="platform_admin" if created_by else "system",
            actor_id=created_by,
            clinic_id=clinic.id,
            after={
                "email": owner_member.email,
                "role": owner_member.role,
                "name": owner_member.name,
            },
            client_ip=ip_address,
        )

        # Attach owner details for response mapping
        clinic.owner_name = data.owner_name  # type: ignore[attr-defined]
        clinic.owner_email = str(data.owner_email)  # type: ignore[attr-defined]
        clinic.owner_phone = data.owner_phone  # type: ignore[attr-defined]

        return clinic

    async def list_clinics(
        self,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[Sequence[Clinic], int]:
        """List clinics with optional name/slug search filtering and telemetry (doctors, tokens 7d)."""
        now = datetime.now(UTC)
        seven_days_ago = now - timedelta(days=7)

        count_query = select(func.count(Clinic.id))

        doctors_subq = (
            select(func.count(Doctor.id))
            .where(
                Doctor.clinic_id == Clinic.id,
                Doctor.active.is_(True),
                Doctor.deleted_at.is_(None),
            )
            .scalar_subquery()
        )

        tokens_subq = (
            select(func.count(Token.id))
            .where(
                Token.clinic_id == Clinic.id,
                Token.created_at >= seven_days_ago,
            )
            .scalar_subquery()
        )

        query = select(
            Clinic,
            doctors_subq.label("doctors_count"),
            tokens_subq.label("tokens_last_7d"),
        )

        if search:
            pattern = f"%{search.strip().lower()}%"
            filter_clause = func.lower(Clinic.name).like(pattern) | func.lower(Clinic.slug).like(
                pattern
            )
            query = query.where(filter_clause)
            count_query = count_query.where(filter_clause)

        query = query.order_by(Clinic.created_at.desc()).limit(limit).offset(offset)

        async with async_tenant_scope(None, bypass=True):
            total_res = await self.session.execute(count_query)
            total = total_res.scalar_one() or 0

            items_res = await self.session.execute(query)
            rows = items_res.all()

        clinics: list[Clinic] = []
        for row in rows:
            if hasattr(row, "Clinic"):
                clinic = row.Clinic
                doc_count = getattr(row, "doctors_count", 0)
                tok_count = getattr(row, "tokens_last_7d", 0)
            elif isinstance(row, tuple) and len(row) >= 3:
                clinic, doc_count, tok_count = row[0], row[1], row[2]
            else:
                clinic = row[0] if isinstance(row, tuple) else row
                doc_count, tok_count = 0, 0

            clinic.doctors_count = doc_count or 0
            clinic.tokens_last_7d = tok_count or 0
            clinics.append(clinic)

        return clinics, total

    async def get_clinic(self, clinic_id: uuid.UUID) -> Clinic:
        """Fetch clinic by ID or raise 404."""
        stmt = select(Clinic).where(Clinic.id == clinic_id)
        res = await self.session.execute(stmt)
        clinic = res.scalar_one_or_none()
        if not clinic:
            raise AppException(
                status_code=404,
                code="CLINIC_NOT_FOUND",
                detail="Clinic not found",
            )
        return clinic

    async def update_status(
        self,
        clinic_id: uuid.UUID,
        new_status: str,
        reason: str,
        changed_by: uuid.UUID | None = None,
        ip_address: str | None = None,
    ) -> Clinic:
        """Update clinic status following the PRD W-007 state machine with audit trail."""
        clinic = await self.get_clinic(clinic_id)
        old_status = clinic.status

        # Validate allowed transitions: trial -> active, active -> suspended, suspended -> active
        valid_transitions = {
            "trial": {"active"},
            "active": {"suspended"},
            "suspended": {"active"},
        }
        if new_status not in valid_transitions.get(old_status, set()):
            raise AppException(
                status_code=400,
                code="INVALID_STATUS_TRANSITION",
                detail=f"Cannot transition clinic from '{old_status}' to '{new_status}'",
            )

        clinic.status = new_status
        await self.session.flush()

        AuditService.record_audit(
            session=self.session,
            action=AuditAction.CLINIC_STATUS_CHANGE,
            entity="clinic",
            entity_id=clinic.id,
            actor_type="platform_admin" if changed_by else "system",
            actor_id=changed_by,
            clinic_id=clinic.id,
            before={"status": old_status},
            after={"status": new_status, "reason": reason},
            client_ip=ip_address,
        )

        return clinic
