import logging
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import forbidden, not_found
from app.models.patient import Patient
from app.models.token import Token
from app.models.visit import Visit
from app.schemas.audit import AuditAction
from app.schemas.auth import CurrentUser, Role
from app.schemas.patient import (
    PatientDetailResponse,
    PatientSearchResult,
    PatientUpdateRequest,
)
from app.services.audit import AuditService

logger = logging.getLogger(__name__)


class PatientService:
    """Domain service managing patient records, search, and profiles."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def search_patients(
        self,
        query: str,
        current_user: CurrentUser,
    ) -> list[PatientSearchResult]:
        """Search patients by name or phone within current clinic scope (PRD §5.3 F-006)."""
        if not current_user.clinic_id:
            raise forbidden(
                code="CLINIC_REQUIRED", detail="Clinic context required for this action"
            )

        if current_user.role not in {Role.RECEPTION, Role.OWNER, Role.DOCTOR}:
            raise forbidden(code="FORBIDDEN", detail="Role not authorized to search patients")

        clean_query = query.strip()
        if len(clean_query) < 2:
            return []

        clinic_id = current_user.clinic_id

        # Prefix / substring match on phone and name
        stmt = (
            select(Patient)
            .where(
                Patient.clinic_id == clinic_id,
                Patient.deleted_at.is_(None),
                or_(
                    Patient.name.ilike(f"%{clean_query}%"),
                    Patient.phone.ilike(f"%{clean_query}%"),
                ),
            )
            .order_by(Patient.name.asc())
            .limit(50)
        )

        res = await self.session.execute(stmt)
        patients = list(res.scalars().all())

        if not patients:
            return []

        patient_ids = [p.id for p in patients]

        # Calculate visit count and last visit date
        # 1. From visits table
        visit_stmt = (
            select(
                Visit.patient_id,
                func.count(Visit.id).label("visit_count"),
                func.max(func.date(Visit.created_at)).label("last_visit_date"),
            )
            .where(
                Visit.clinic_id == clinic_id,
                Visit.patient_id.in_(patient_ids),
            )
            .group_by(Visit.patient_id)
        )
        visit_res = await self.session.execute(visit_stmt)
        visit_stats = {
            row[0]: {"visit_count": row[1], "last_visit_date": row[2]} for row in visit_res.all()
        }

        # 2. From completed/serviced tokens if visits don't exist
        token_stmt = (
            select(
                Token.patient_id,
                func.count(Token.id).label("token_count"),
                func.max(Token.visit_date).label("last_token_date"),
            )
            .where(
                Token.clinic_id == clinic_id,
                Token.patient_id.in_(patient_ids),
                Token.status.in_(["done", "serving", "arrived"]),
            )
            .group_by(Token.patient_id)
        )
        token_res = await self.session.execute(token_stmt)
        token_stats = {
            row[0]: {"token_count": row[1], "last_token_date": row[2]} for row in token_res.all()
        }

        results: list[PatientSearchResult] = []
        for p in patients:
            v_stat = visit_stats.get(p.id)
            t_stat = token_stats.get(p.id)

            visit_count = 0
            last_visit = None

            if v_stat and v_stat["visit_count"] > 0:
                visit_count = v_stat["visit_count"]
                last_visit = v_stat["last_visit_date"]
            elif t_stat and t_stat["token_count"] > 0:
                visit_count = t_stat["token_count"]
                last_visit = t_stat["last_token_date"]

            results.append(
                PatientSearchResult(
                    id=p.id,
                    name=p.name,
                    phone=p.phone,
                    date_of_birth=p.date_of_birth,
                    gender=p.gender,
                    visit_count=visit_count,
                    last_visit_date=last_visit,
                )
            )

        return results

    async def get_patient_profile(
        self,
        patient_id: uuid.UUID,
        current_user: CurrentUser,
    ) -> PatientDetailResponse:
        """Retrieve full patient profile and visit statistics (PRD §5.3 F-006)."""
        if not current_user.clinic_id:
            raise forbidden(
                code="CLINIC_REQUIRED", detail="Clinic context required for this action"
            )

        if current_user.role not in {Role.RECEPTION, Role.OWNER, Role.DOCTOR}:
            raise forbidden(code="FORBIDDEN", detail="Role not authorized to view patient profile")

        clinic_id = current_user.clinic_id

        stmt = select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
            Patient.deleted_at.is_(None),
        )
        res = await self.session.execute(stmt)
        patient = res.scalar_one_or_none()

        if not patient:
            raise not_found(code="PATIENT_NOT_FOUND", detail="Patient not found in this clinic")

        # Stats
        visit_stmt = select(
            func.count(Visit.id).label("visit_count"),
            func.max(func.date(Visit.created_at)).label("last_visit_date"),
        ).where(
            Visit.clinic_id == clinic_id,
            Visit.patient_id == patient_id,
        )
        visit_res = await self.session.execute(visit_stmt)
        v_row = visit_res.first()

        visit_count = v_row[0] if v_row else 0
        last_visit_date = v_row[1] if v_row else None

        if visit_count == 0:
            token_stmt = select(
                func.count(Token.id).label("token_count"),
                func.max(Token.visit_date).label("last_token_date"),
            ).where(
                Token.clinic_id == clinic_id,
                Token.patient_id == patient_id,
                Token.status.in_(["done", "serving", "arrived"]),
            )
            token_res = await self.session.execute(token_stmt)
            t_row = token_res.first()
            if t_row and t_row[0] > 0:
                visit_count = t_row[0]
                last_visit_date = t_row[1]

        return PatientDetailResponse(
            id=patient.id,
            clinic_id=patient.clinic_id,
            name=patient.name,
            phone=patient.phone,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            notes=patient.notes,
            visit_count=visit_count,
            last_visit_date=last_visit_date,
            created_at=patient.created_at,
            updated_at=patient.updated_at,
        )

    async def update_patient_profile(
        self,
        patient_id: uuid.UUID,
        data: PatientUpdateRequest,
        current_user: CurrentUser,
    ) -> PatientDetailResponse:
        """Update patient profile with mandatory audit logging (PRD §5.3 F-006)."""
        if not current_user.clinic_id:
            raise forbidden(
                code="CLINIC_REQUIRED", detail="Clinic context required for this action"
            )

        if current_user.role not in {Role.RECEPTION, Role.OWNER}:
            raise forbidden(
                code="FORBIDDEN",
                detail="Only reception and clinic owner can edit patient profiles",
            )

        clinic_id = current_user.clinic_id

        stmt = select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
            Patient.deleted_at.is_(None),
        )
        res = await self.session.execute(stmt)
        patient = res.scalar_one_or_none()

        if not patient:
            raise not_found(code="PATIENT_NOT_FOUND", detail="Patient not found in this clinic")

        before_state = {
            "name": patient.name,
            "phone": patient.phone,
            "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
            "gender": patient.gender,
            "notes": patient.notes,
        }

        patient.name = data.name.strip()
        patient.phone = data.phone
        patient.date_of_birth = data.date_of_birth
        patient.gender = data.gender
        patient.notes = data.notes

        await self.session.flush()

        after_state = {
            "name": patient.name,
            "phone": patient.phone,
            "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
            "gender": patient.gender,
            "notes": patient.notes,
        }

        AuditService.record_audit(
            session=self.session,
            action=AuditAction.PATIENT_EDIT,
            entity="patient",
            entity_id=patient.id,
            actor_type="staff",
            actor_id=current_user.user_id,
            clinic_id=clinic_id,
            before=before_state,
            after=after_state,
        )

        await self.session.commit()
        await self.session.refresh(patient)

        return await self.get_patient_profile(patient_id, current_user)
