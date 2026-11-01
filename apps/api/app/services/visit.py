import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import bad_request, forbidden, not_found
from app.models.clinic import ClinicSettings
from app.models.doctor import Doctor
from app.models.member import ClinicMember
from app.models.patient import Patient
from app.models.token import Token
from app.models.visit import Visit
from app.schemas.audit import AuditAction
from app.schemas.auth import CurrentUser, Role
from app.schemas.visit import (
    PatientHistoryResponse,
    VisitCreateRequest,
    VisitListItem,
    VisitUpdateRequest,
)
from app.services.audit import AuditService

logger = logging.getLogger(__name__)


class VisitService:
    """Domain service managing patient clinical encounters, history timelines, and visit notes."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _resolve_doctor_id(
        self,
        clinic_id: uuid.UUID,
        current_user: CurrentUser,
    ) -> uuid.UUID:
        if current_user.role == Role.DOCTOR:
            if current_user.doctor_id:
                return current_user.doctor_id

            stmt = select(ClinicMember.doctor_id).where(
                ClinicMember.clinic_id == clinic_id,
                ClinicMember.user_id == current_user.user_id,
                ClinicMember.deleted_at.is_(None),
            )
            res = await self.session.execute(stmt)
            doc_id = res.scalar_one_or_none()
            if doc_id:
                return doc_id
            raise forbidden(code="NO_DOCTOR_PROFILE", detail="No doctor profile assigned to user.")

        # Owner role fallback
        doc_stmt = (
            select(Doctor.id).where(Doctor.clinic_id == clinic_id, Doctor.active.is_(True)).limit(1)
        )
        res = await self.session.execute(doc_stmt)
        first_doc = res.scalar_one_or_none()
        if first_doc:
            return first_doc
        raise bad_request(code="NO_DOCTOR", detail="No doctor found for this clinic.")

    async def get_patient_history(
        self,
        clinic_id: uuid.UUID,
        patient_id: uuid.UUID,
        current_user: CurrentUser,
    ) -> PatientHistoryResponse:
        """Retrieve full visit timeline for a patient (PRD §5.3 F-008, W-009)."""
        if current_user.role not in {Role.DOCTOR, Role.OWNER}:
            raise forbidden(
                code="FORBIDDEN", detail="Role not authorized to access clinical records."
            )

        # 1. Verify patient exists in clinic
        p_stmt = select(Patient).where(
            Patient.id == patient_id,
            Patient.clinic_id == clinic_id,
            Patient.deleted_at.is_(None),
        )
        p_res = await self.session.execute(p_stmt)
        patient = p_res.scalar_one_or_none()
        if not patient:
            raise not_found(code="PATIENT_NOT_FOUND", detail="Patient not found in this clinic.")

        # 2. Check clinic setting for sharing advice
        s_stmt = select(ClinicSettings).where(ClinicSettings.clinic_id == clinic_id)
        s_res = await self.session.execute(s_stmt)
        settings = s_res.scalar_one_or_none()
        share_setting = settings.share_advice_with_patient if settings else False

        # 3. Query all visits for patient newest first
        v_stmt = (
            select(Visit, Doctor, Token)
            .join(Doctor, Visit.doctor_id == Doctor.id)
            .outerjoin(Token, Visit.token_id == Token.id)
            .where(
                Visit.clinic_id == clinic_id,
                Visit.patient_id == patient_id,
            )
            .order_by(Visit.created_at.desc())
        )
        v_res = await self.session.execute(v_stmt)
        rows = v_res.all()

        visit_items: list[VisitListItem] = []
        for visit, doctor, token in rows:
            visit_items.append(
                VisitListItem(
                    id=visit.id,
                    doctor_id=doctor.id,
                    doctor_name=doctor.name,
                    complaint=visit.complaint,
                    notes=visit.notes,  # Private to staff
                    medicines_advice=visit.medicines_advice,
                    share_with_patient=visit.share_with_patient,
                    token_id=visit.token_id,
                    token_number=token.number if token else None,
                    created_at=visit.created_at,
                )
            )

        return PatientHistoryResponse(
            patient_id=patient.id,
            patient_name=patient.name,
            phone=patient.phone,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
            notes=patient.notes,
            share_advice_clinic_setting=share_setting,
            visits=visit_items,
        )

    async def create_or_update_visit_note(
        self,
        clinic_id: uuid.UUID,
        payload: VisitCreateRequest,
        current_user: CurrentUser,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> VisitListItem:
        """Create or update a visit encounter note (PRD §5.3 F-008, W-009)."""
        if current_user.role not in {Role.DOCTOR, Role.OWNER}:
            raise forbidden(code="FORBIDDEN", detail="Role not authorized to create visit records.")

        # 1. Patient check
        p_stmt = select(Patient).where(
            Patient.id == payload.patient_id,
            Patient.clinic_id == clinic_id,
            Patient.deleted_at.is_(None),
        )
        p_res = await self.session.execute(p_stmt)
        patient = p_res.scalar_one_or_none()
        if not patient:
            raise not_found(code="PATIENT_NOT_FOUND", detail="Patient not found in this clinic.")

        # 2. Doctor resolve
        effective_doctor_id = await self._resolve_doctor_id(clinic_id, current_user)
        d_stmt = select(Doctor).where(
            Doctor.id == effective_doctor_id, Doctor.clinic_id == clinic_id
        )
        d_res = await self.session.execute(d_stmt)
        doctor = d_res.scalar_one_or_none()
        if not doctor:
            raise not_found(code="DOCTOR_NOT_FOUND", detail="Doctor not found in this clinic.")

        # 3. Check if visit already exists for token_id
        existing_visit: Visit | None = None
        if payload.token_id:
            tok_stmt = select(Visit).where(
                Visit.clinic_id == clinic_id,
                Visit.token_id == payload.token_id,
            )
            tok_res = await self.session.execute(tok_stmt)
            existing_visit = tok_res.scalar_one_or_none()

        action = AuditAction.VISIT_EDIT if existing_visit else AuditAction.VISIT_CREATE

        if existing_visit:
            existing_visit.complaint = payload.complaint
            existing_visit.notes = payload.notes
            existing_visit.medicines_advice = payload.medicines_advice
            existing_visit.share_with_patient = payload.share_with_patient
            visit_record = existing_visit
        else:
            visit_record = Visit(
                id=uuid.uuid4(),
                clinic_id=clinic_id,
                patient_id=payload.patient_id,
                doctor_id=effective_doctor_id,
                token_id=payload.token_id,
                complaint=payload.complaint,
                notes=payload.notes,
                medicines_advice=payload.medicines_advice,
                share_with_patient=payload.share_with_patient,
                created_by=current_user.user_id,
                created_at=datetime.now(UTC),
            )
            self.session.add(visit_record)

        await self.session.flush()

        AuditService.record_audit(
            session=self.session,
            action=action,
            entity="visit",
            entity_id=visit_record.id,
            actor_type="staff",
            actor_id=current_user.user_id,
            clinic_id=clinic_id,
            before=None,
            after={
                "patient_id": str(payload.patient_id),
                "doctor_id": str(effective_doctor_id),
                "token_id": str(payload.token_id) if payload.token_id else None,
                "share_with_patient": payload.share_with_patient,
            },
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()
        await self.session.refresh(visit_record)

        # Get token number if linked
        token_num = None
        if visit_record.token_id:
            t_stmt = select(Token.number).where(Token.id == visit_record.token_id)
            t_res = await self.session.execute(t_stmt)
            token_num = t_res.scalar_one_or_none()

        return VisitListItem(
            id=visit_record.id,
            doctor_id=doctor.id,
            doctor_name=doctor.name,
            complaint=visit_record.complaint,
            notes=visit_record.notes,
            medicines_advice=visit_record.medicines_advice,
            share_with_patient=visit_record.share_with_patient,
            token_id=visit_record.token_id,
            token_number=token_num,
            created_at=visit_record.created_at,
        )

    async def update_visit_note(
        self,
        clinic_id: uuid.UUID,
        visit_id: uuid.UUID,
        payload: VisitUpdateRequest,
        current_user: CurrentUser,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> VisitListItem:
        """Update an existing clinical visit note (PRD §5.3 F-008, W-009)."""
        if current_user.role not in {Role.DOCTOR, Role.OWNER}:
            raise forbidden(code="FORBIDDEN", detail="Role not authorized to update visit records.")

        v_stmt = (
            select(Visit, Doctor)
            .join(Doctor, Visit.doctor_id == Doctor.id)
            .where(Visit.id == visit_id, Visit.clinic_id == clinic_id)
        )
        v_res = await self.session.execute(v_stmt)
        row = v_res.first()
        if not row:
            raise not_found(code="VISIT_NOT_FOUND", detail="Visit record not found.")

        visit, doctor = row
        visit.complaint = payload.complaint
        visit.notes = payload.notes
        visit.medicines_advice = payload.medicines_advice
        visit.share_with_patient = payload.share_with_patient

        await self.session.flush()

        AuditService.record_audit(
            session=self.session,
            action=AuditAction.VISIT_EDIT,
            entity="visit",
            entity_id=visit.id,
            actor_type="staff",
            actor_id=current_user.user_id,
            clinic_id=clinic_id,
            before=None,
            after={
                "complaint": payload.complaint,
                "share_with_patient": payload.share_with_patient,
            },
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()
        await self.session.refresh(visit)

        token_num = None
        if visit.token_id:
            t_stmt = select(Token.number).where(Token.id == visit.token_id)
            t_res = await self.session.execute(t_stmt)
            token_num = t_res.scalar_one_or_none()

        return VisitListItem(
            id=visit.id,
            doctor_id=doctor.id,
            doctor_name=doctor.name,
            complaint=visit.complaint,
            notes=visit.notes,
            medicines_advice=visit.medicines_advice,
            share_with_patient=visit.share_with_patient,
            token_id=visit.token_id,
            token_number=token_num,
            created_at=visit.created_at,
        )
