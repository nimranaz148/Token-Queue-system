import logging
import secrets
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import (
    bad_request,
    conflict,
    forbidden,
    not_found,
    unprocessable_entity,
)
from app.core.phone import normalize_phone
from app.integrations.realtime import SupabaseRealtimeClient
from app.integrations.turnstile import TurnstileService
from app.models.clinic import Clinic, ClinicSettings
from app.models.doctor import Doctor, DoctorSchedule
from app.models.patient import Patient
from app.models.token import Token, TokenCounter, TokenEvent
from app.schemas.auth import CurrentUser, Role
from app.schemas.token import (
    PublicClinicInfoResponse,
    PublicDoctorInfo,
    PublicDoctorSchedule,
    ReceptionTokenListItem,
    TokenBookingRequest,
    TokenBookingResponse,
    TokenCancelResponse,
    TokenDetailsResponse,
)
from app.services.audit import AuditService

logger = logging.getLogger(__name__)


class TokenService:
    """Domain service for patient token issuance, queue progression, and lifecycle management."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_public_clinic_info(self, slug: str) -> PublicClinicInfoResponse:
        """Retrieve public clinic profile, OPD doctors, and schedules (PRD §5.3 F-001)."""
        clinic_stmt = select(Clinic).where(Clinic.slug == slug)
        res = await self.session.execute(clinic_stmt)
        clinic = res.scalar_one_or_none()
        if not clinic:
            raise not_found(code="CLINIC_NOT_FOUND", detail=f"Clinic with slug '{slug}' not found")

        if clinic.status == "suspended":
            raise forbidden(code="CLINIC_SUSPENDED", detail="This clinic is currently suspended.")

        # Settings
        settings_stmt = select(ClinicSettings).where(ClinicSettings.clinic_id == clinic.id)
        settings_res = await self.session.execute(settings_stmt)
        clinic_settings = settings_res.scalar_one_or_none()
        online_booking_enabled = clinic_settings.online_booking_enabled if clinic_settings else True

        # Doctors
        docs_stmt = (
            select(Doctor)
            .where(
                Doctor.clinic_id == clinic.id,
                Doctor.active.is_(True),
                Doctor.deleted_at.is_(None),
            )
            .order_by(Doctor.name)
        )
        docs_res = await self.session.execute(docs_stmt)
        doctors = docs_res.scalars().all()

        public_doctors: list[PublicDoctorInfo] = []
        for doc in doctors:
            sched_stmt = (
                select(DoctorSchedule)
                .where(DoctorSchedule.doctor_id == doc.id)
                .order_by(DoctorSchedule.weekday, DoctorSchedule.start_time)
            )
            sched_res = await self.session.execute(sched_stmt)
            schedules = sched_res.scalars().all()

            public_doctors.append(
                PublicDoctorInfo(
                    id=doc.id,
                    name=doc.name,
                    specialty=doc.specialty,
                    daily_online_limit=doc.daily_online_limit,
                    consult_minutes=doc.consult_minutes,
                    schedules=[
                        PublicDoctorSchedule(
                            weekday=s.weekday,
                            start_time=s.start_time.strftime("%H:%M"),
                            end_time=s.end_time.strftime("%H:%M"),
                        )
                        for s in schedules
                    ],
                )
            )

        return PublicClinicInfoResponse(
            id=clinic.id,
            name=clinic.name,
            slug=clinic.slug,
            time_zone=clinic.time_zone,
            address=clinic.address,
            phone=clinic.phone,
            online_booking_enabled=online_booking_enabled,
            doctors=public_doctors,
        )

    async def book_token(
        self,
        slug: str,
        payload: TokenBookingRequest,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> TokenBookingResponse:
        """Issue an online token for an OPD visit inside an atomic transaction (F-001, W-001).

        Guarantees:
        - Turnstile anti-bot verification.
        - E.164 phone normalisation.
        - Doctor daily online limit check (409 DAILY_LIMIT_REACHED).
        - Active duplicate check (409 ACTIVE_TOKEN_EXISTS with existing link).
        - Sequential token numbering via row lock on token_counters.
        - TokenEvent + Audit log creation.
        """
        # 1. Turnstile anti-abuse check
        await TurnstileService.verify_token(payload.turnstile_token, client_ip=client_ip)

        # 2. Clinic lookup and status check
        clinic_stmt = select(Clinic).where(Clinic.slug == slug)
        clinic_res = await self.session.execute(clinic_stmt)
        clinic = clinic_res.scalar_one_or_none()
        if not clinic:
            raise not_found(code="CLINIC_NOT_FOUND", detail=f"Clinic with slug '{slug}' not found")

        if clinic.status == "suspended":
            raise forbidden(code="CLINIC_SUSPENDED", detail="This clinic is currently suspended.")

        # 3. Clinic settings check (online booking enabled)
        settings_stmt = select(ClinicSettings).where(ClinicSettings.clinic_id == clinic.id)
        settings_res = await self.session.execute(settings_stmt)
        clinic_settings = settings_res.scalar_one_or_none()
        if clinic_settings and not clinic_settings.online_booking_enabled:
            raise conflict(
                code="BOOKING_CLOSED",
                detail="Online booking is currently disabled for this clinic.",
            )

        # 4. Visit date validation (must be today or tomorrow)
        today = date.today()
        tomorrow = today + timedelta(days=1)
        if payload.visit_date < today or payload.visit_date > tomorrow:
            raise unprocessable_entity(
                code="INVALID_VISIT_DATE",
                detail=f"Booking is only allowed for today ({today}) or tomorrow ({tomorrow}).",
            )

        # 5. Doctor lookup and active status
        doc_stmt = select(Doctor).where(
            Doctor.id == payload.doctor_id,
            Doctor.clinic_id == clinic.id,
            Doctor.active.is_(True),
            Doctor.deleted_at.is_(None),
        )
        doc_res = await self.session.execute(doc_stmt)
        doctor = doc_res.scalar_one_or_none()
        if not doctor:
            raise not_found(
                code="DOCTOR_NOT_FOUND",
                detail="Selected doctor was not found or is currently inactive.",
            )

        # 6. Doctor schedule check for the chosen weekday
        weekday = payload.visit_date.weekday()
        sched_stmt = select(DoctorSchedule).where(
            DoctorSchedule.doctor_id == doctor.id,
            DoctorSchedule.weekday == weekday,
        )
        sched_res = await self.session.execute(sched_stmt)
        schedule = sched_res.scalars().first()

        # Check total schedules for this doctor
        any_sched_stmt = (
            select(func.count())
            .select_from(DoctorSchedule)
            .where(DoctorSchedule.doctor_id == doctor.id)
        )
        total_scheds = (await self.session.execute(any_sched_stmt)).scalar() or 0
        if total_scheds > 0 and schedule is None:
            raise unprocessable_entity(
                code="NO_OPD_SCHEDULE",
                detail=f"Doctor {doctor.name} has no OPD schedule on {payload.visit_date.strftime('%A')}.",
            )

        # 7. Daily online limit check
        if doctor.daily_online_limit is not None and doctor.daily_online_limit > 0:
            count_stmt = (
                select(func.count())
                .select_from(Token)
                .where(
                    Token.clinic_id == clinic.id,
                    Token.doctor_id == doctor.id,
                    Token.visit_date == payload.visit_date,
                    Token.source == "online",
                    Token.status != "cancelled",
                )
            )
            count_res = await self.session.execute(count_stmt)
            active_count = count_res.scalar() or 0
            if active_count >= doctor.daily_online_limit:
                raise conflict(
                    code="DAILY_LIMIT_REACHED",
                    detail=f"Daily online booking limit ({doctor.daily_online_limit}) reached for Dr. {doctor.name}.",
                )

        # 8. Normalise phone to E.164
        normalized_phone = normalize_phone(payload.phone)

        # 9. Active duplicate check
        pat_stmt = select(Patient).where(
            Patient.clinic_id == clinic.id,
            Patient.phone == normalized_phone,
            Patient.deleted_at.is_(None),
        )
        pat_res = await self.session.execute(pat_stmt)
        patient = pat_res.scalar_one_or_none()

        if patient:
            dup_stmt = select(Token).where(
                Token.clinic_id == clinic.id,
                Token.doctor_id == doctor.id,
                Token.visit_date == payload.visit_date,
                Token.patient_id == patient.id,
                Token.status.in_(["booked", "arrived", "serving", "hold"]),
            )
            dup_res = await self.session.execute(dup_stmt)
            existing_token = dup_res.scalar_one_or_none()
            if existing_token:
                raise conflict(
                    code="ACTIVE_TOKEN_EXISTS",
                    detail=f"An active token #{existing_token.number} already exists for this phone and doctor today.",
                    extra={
                        "existing_public_code": existing_token.public_code,
                        "existing_token_url": f"/t/{existing_token.public_code}",
                        "token_number": existing_token.number,
                    },
                )
        else:
            patient = Patient(
                clinic_id=clinic.id,
                phone=normalized_phone,
                name=payload.patient_name.strip(),
            )
            self.session.add(patient)
            await self.session.flush()

        # Update patient name if changed
        if patient.name != payload.patient_name.strip():
            patient.name = payload.patient_name.strip()

        # 10. Atomic sequence allocation via row lock on token_counters
        # Check if counter row exists
        counter_stmt = (
            select(TokenCounter)
            .where(
                TokenCounter.clinic_id == clinic.id,
                TokenCounter.doctor_id == doctor.id,
                TokenCounter.visit_date == payload.visit_date,
            )
            .with_for_update()
        )
        counter_res = await self.session.execute(counter_stmt)
        counter = counter_res.scalar_one_or_none()

        if not counter:
            counter = TokenCounter(
                clinic_id=clinic.id,
                doctor_id=doctor.id,
                visit_date=payload.visit_date,
                last_number=0,
            )
            self.session.add(counter)
            await self.session.flush()
            # Lock the newly added row
            counter_res = await self.session.execute(counter_stmt)
            counter = counter_res.scalar_one_or_none() or counter

        new_number = counter.last_number + 1
        counter.last_number = new_number

        # 11. Generate public code and compute estimated time
        public_code = secrets.token_urlsafe(16)
        estimated_at: datetime | None = None
        if schedule and schedule.start_time:
            consult_mins = doctor.consult_minutes or 10
            delay_mins = (new_number - 1) * consult_mins
            base_time = datetime.combine(payload.visit_date, schedule.start_time, tzinfo=UTC)
            estimated_at = base_time + timedelta(minutes=delay_mins)

        # 12. Insert Token
        now = datetime.now(UTC)
        token = Token(
            id=uuid.uuid4(),
            clinic_id=clinic.id,
            doctor_id=doctor.id,
            patient_id=patient.id,
            visit_date=payload.visit_date,
            number=new_number,
            position=Decimal(new_number),
            source="online",
            status="booked",
            public_code=public_code,
            estimated_at=estimated_at,
            created_at=now,
            updated_at=now,
        )
        self.session.add(token)
        await self.session.flush()

        # 13. Insert TokenEvent
        token_event = TokenEvent(
            token_id=token.id,
            clinic_id=clinic.id,
            from_status=None,
            to_status="booked",
            actor_type="patient",
            actor_id=None,
        )
        self.session.add(token_event)

        # 14. Record Audit Log
        AuditService.record_audit(
            session=self.session,
            action="token.create",
            entity="token",
            entity_id=token.id,
            actor_type="public",
            actor_id=None,
            clinic_id=clinic.id,
            client_ip=client_ip,
            request_id=request_id,
            after={
                "token_id": str(token.id),
                "number": new_number,
                "doctor_id": str(doctor.id),
                "visit_date": str(payload.visit_date),
                "source": "online",
                "status": "booked",
            },
        )

        await self.session.commit()
        await self.session.refresh(token)

        # Broadcast queue update via Supabase Realtime (I-002, Rule 10)
        try:
            realtime_client = SupabaseRealtimeClient()
            await realtime_client.broadcast_queue_update(
                clinic_id=clinic.id,
                doctor_id=doctor.id,
                event="token.created",
                token_number=token.number,
                total_waiting=token.number,
                non_blocking=True,
            )
        except Exception as exc:
            logger.warning("Realtime broadcast skipped on book_token: %s", exc)

        return TokenBookingResponse(
            id=token.id,
            number=token.number,
            public_code=token.public_code,
            status=token.status,
            source=token.source,
            visit_date=token.visit_date,
            doctor_id=doctor.id,
            doctor_name=doctor.name,
            clinic_name=clinic.name,
            clinic_slug=clinic.slug,
            position=token.position,
            estimated_at=token.estimated_at,
            created_at=token.created_at,
        )

    async def get_token_by_public_code(self, public_code: str) -> TokenDetailsResponse:
        """Fetch token state, wait metrics, and doctor info for Token Confirm / Live Queue (F-002, F-003)."""
        token_stmt = select(Token).where(Token.public_code == public_code)
        token_res = await self.session.execute(token_stmt)
        token = token_res.scalar_one_or_none()
        if not token:
            raise not_found(
                code="TOKEN_NOT_FOUND",
                detail=f"Token with public code '{public_code}' was not found.",
            )

        clinic_stmt = select(Clinic).where(Clinic.id == token.clinic_id)
        clinic = (await self.session.execute(clinic_stmt)).scalar_one_or_none()

        doc_stmt = select(Doctor).where(Doctor.id == token.doctor_id)
        doctor = (await self.session.execute(doc_stmt)).scalar_one_or_none()

        # Count people ahead (status in booked/arrived with position < token.position)
        ahead_stmt = (
            select(func.count())
            .select_from(Token)
            .where(
                Token.clinic_id == token.clinic_id,
                Token.doctor_id == token.doctor_id,
                Token.visit_date == token.visit_date,
                Token.status.in_(["booked", "arrived"]),
                Token.position < token.position,
            )
        )
        people_ahead = (await self.session.execute(ahead_stmt)).scalar() or 0

        # Current serving token number
        serving_stmt = (
            select(Token.number)
            .where(
                Token.clinic_id == token.clinic_id,
                Token.doctor_id == token.doctor_id,
                Token.visit_date == token.visit_date,
                Token.status == "serving",
            )
            .limit(1)
        )
        current_serving = (await self.session.execute(serving_stmt)).scalar_one_or_none()

        # Calculate estimated wait minutes (PRD §5.3 F-003)
        consult_mins = doctor.consult_minutes or 10 if doctor else 10
        estimated_wait_minutes = people_ahead * consult_mins

        return TokenDetailsResponse(
            id=token.id,
            number=token.number,
            public_code=token.public_code,
            status=token.status,
            source=token.source,
            visit_date=token.visit_date,
            doctor_id=token.doctor_id,
            doctor_name=doctor.name if doctor else "Doctor",
            specialty=doctor.specialty if doctor else None,
            clinic_id=token.clinic_id,
            clinic_name=clinic.name if clinic else "Clinic",
            clinic_slug=clinic.slug if clinic else "clinic",
            position=token.position,
            estimated_at=token.estimated_at,
            people_ahead=people_ahead,
            estimated_wait_minutes=estimated_wait_minutes,
            current_serving_number=current_serving,
            cancelled_reason=token.cancelled_reason,
            created_at=token.created_at,
        )

    async def cancel_token_by_public_code(
        self,
        public_code: str,
        reason: str = "Cancelled by patient",
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> TokenCancelResponse:
        """Cancel an issued token from Token Confirm view (W-005, PRD §5.3 F-002).

        Rules:
        - Only tokens in 'booked' or 'arrived' status can be cancelled.
        - Number is not reused.
        - Writes token_events and audit row.
        """
        token_stmt = select(Token).where(Token.public_code == public_code)
        token_res = await self.session.execute(token_stmt)
        token = token_res.scalar_one_or_none()
        if not token:
            raise not_found(
                code="TOKEN_NOT_FOUND",
                detail=f"Token with public code '{public_code}' was not found.",
            )

        if token.status not in {"booked", "arrived"}:
            raise conflict(
                code="CANNOT_CANCEL",
                detail=f"Token with status '{token.status}' cannot be cancelled.",
            )

        old_status = token.status
        token.status = "cancelled"
        token.cancelled_reason = reason

        token_event = TokenEvent(
            token_id=token.id,
            clinic_id=token.clinic_id,
            from_status=old_status,
            to_status="cancelled",
            actor_type="patient",
            actor_id=None,
        )
        self.session.add(token_event)

        AuditService.record_audit(
            session=self.session,
            action="token.cancel",
            entity="token",
            entity_id=token.id,
            actor_type="patient",
            actor_id=None,
            clinic_id=token.clinic_id,
            before={"status": old_status},
            after={"status": "cancelled", "reason": reason},
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()
        await self.session.refresh(token)

        # Broadcast queue update via Supabase Realtime (I-002, Rule 10)
        try:
            realtime_client = SupabaseRealtimeClient()
            await realtime_client.broadcast_queue_update(
                clinic_id=token.clinic_id,
                doctor_id=token.doctor_id,
                event="token.cancelled",
                token_number=token.number,
                non_blocking=True,
            )
        except Exception as exc:
            logger.warning("Realtime broadcast skipped on cancel_token: %s", exc)

        return TokenCancelResponse(
            id=token.id,
            number=token.number,
            public_code=token.public_code,
            status=token.status,
            cancelled_reason=token.cancelled_reason,
            message="Token cancelled successfully.",
        )

    async def list_reception_tokens(
        self,
        clinic_id: uuid.UUID,
        current_user: CurrentUser,
        target_date: date,
        doctor_id: uuid.UUID | None = None,
        status_filter: list[str] | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[ReceptionTokenListItem], int]:
        """List tokens for Aaj ki List reception view (PRD §5.3 F-004).

        Permissions:
        - reception, owner: full clinic view.
        - doctor: own tokens only (token.doctor_id == current_user.doctor_id).
        - others: 403 FORBIDDEN.
        """
        role = current_user.role
        if role not in (Role.RECEPTION, Role.OWNER, Role.DOCTOR):
            raise forbidden(
                code="FORBIDDEN",
                detail="Only reception, owner, or doctor can access Aaj ki List.",
            )

        # Doctor can only see their own queue
        if role == Role.DOCTOR:
            if not current_user.doctor_id:
                raise forbidden(
                    code="DOCTOR_PROFILE_MISSING",
                    detail="Doctor profile not associated with user.",
                )
            if doctor_id and doctor_id != current_user.doctor_id:
                raise forbidden(
                    code="FORBIDDEN_DOCTOR_QUEUE",
                    detail="Doctors can only view their own token queue.",
                )
            doctor_id = current_user.doctor_id

        stmt = (
            select(Token, Patient, Doctor)
            .join(Patient, Token.patient_id == Patient.id)
            .join(Doctor, Token.doctor_id == Doctor.id)
            .where(
                Token.clinic_id == clinic_id,
                Token.visit_date == target_date,
            )
        )

        if doctor_id:
            stmt = stmt.where(Token.doctor_id == doctor_id)

        if status_filter:
            stmt = stmt.where(Token.status.in_(status_filter))

        if search and len(search.strip()) >= 2:
            s = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(Patient.name).like(s),
                    Patient.phone.like(s),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar() or 0

        # Sort by position ascending
        stmt = stmt.order_by(Token.position.asc(), Token.number.asc()).limit(limit).offset(offset)
        rows_res = await self.session.execute(stmt)
        rows = rows_res.all()

        items: list[ReceptionTokenListItem] = []
        for token, patient, doctor in rows:
            raw_phone = patient.phone or ""
            masked_phone = f"***{raw_phone[-4:]}" if len(raw_phone) >= 4 else "***"

            items.append(
                ReceptionTokenListItem(
                    id=token.id,
                    number=token.number,
                    patient_id=patient.id,
                    patient_name=patient.name,
                    phone=masked_phone,
                    source=token.source,
                    status=token.status,
                    doctor_id=doctor.id,
                    doctor_name=doctor.name,
                    visit_date=token.visit_date,
                    position=token.position,
                    arrived_at=token.arrived_at,
                    called_at=token.called_at,
                    completed_at=token.completed_at,
                    cancelled_reason=token.cancelled_reason,
                    created_at=token.created_at,
                )
            )

        return items, total

    async def mark_token_arrived(
        self,
        clinic_id: uuid.UUID,
        token_id: uuid.UUID,
        current_user: CurrentUser,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> ReceptionTokenListItem:
        """Mark a booked token as arrived (PRD §5.3 F-004, W-003).

        Permissions: reception, owner.
        Rule: Only allowed from status 'booked'.
        """
        if current_user.role not in (Role.RECEPTION, Role.OWNER):
            raise forbidden(
                code="FORBIDDEN",
                detail="Only reception or owner can mark tokens arrived.",
            )

        stmt = (
            select(Token, Patient, Doctor)
            .join(Patient, Token.patient_id == Patient.id)
            .join(Doctor, Token.doctor_id == Doctor.id)
            .where(
                Token.id == token_id,
                Token.clinic_id == clinic_id,
            )
        )
        res = await self.session.execute(stmt)
        row = res.one_or_none()
        if not row:
            raise not_found(
                code="TOKEN_NOT_FOUND",
                detail=f"Token with ID {token_id} not found.",
            )

        token, patient, doctor = row

        if token.status != "booked":
            raise bad_request(
                code="INVALID_STATUS_TRANSITION",
                detail=f"Cannot mark token arrived from status '{token.status}'. Must be 'booked'.",
            )

        old_status = token.status
        token.status = "arrived"
        token.arrived_at = datetime.now(UTC)

        token_event = TokenEvent(
            token_id=token.id,
            clinic_id=token.clinic_id,
            from_status=old_status,
            to_status="arrived",
            actor_type="staff",
            actor_id=current_user.user_id,
        )
        self.session.add(token_event)

        AuditService.record_audit(
            session=self.session,
            action="token.arrive",
            entity="token",
            entity_id=token.id,
            actor_type="staff",
            actor_id=current_user.user_id,
            clinic_id=token.clinic_id,
            before={"status": old_status},
            after={"status": "arrived", "arrived_at": token.arrived_at.isoformat()},
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()
        await self.session.refresh(token)

        try:
            realtime_client = SupabaseRealtimeClient()
            await realtime_client.broadcast_queue_update(
                clinic_id=token.clinic_id,
                doctor_id=token.doctor_id,
                event="token.arrived",
                token_number=token.number,
                non_blocking=True,
            )
        except Exception as exc:
            logger.warning("Realtime broadcast skipped on mark_token_arrived: %s", exc)

        raw_phone = patient.phone or ""
        masked_phone = f"***{raw_phone[-4:]}" if len(raw_phone) >= 4 else "***"

        return ReceptionTokenListItem(
            id=token.id,
            number=token.number,
            patient_id=patient.id,
            patient_name=patient.name,
            phone=masked_phone,
            source=token.source,
            status=token.status,
            doctor_id=doctor.id,
            doctor_name=doctor.name,
            visit_date=token.visit_date,
            position=token.position,
            arrived_at=token.arrived_at,
            called_at=token.called_at,
            completed_at=token.completed_at,
            cancelled_reason=token.cancelled_reason,
            created_at=token.created_at,
        )

    async def cancel_token_by_staff(
        self,
        clinic_id: uuid.UUID,
        token_id: uuid.UUID,
        reason: str,
        current_user: CurrentUser,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> ReceptionTokenListItem:
        """Cancel a token by staff with mandatory reason (PRD §5.3 F-004, W-005).

        Permissions: reception, owner.
        """
        if current_user.role not in (Role.RECEPTION, Role.OWNER):
            raise forbidden(
                code="FORBIDDEN",
                detail="Only reception or owner can cancel tokens.",
            )

        if not reason or len(reason.strip()) < 2:
            raise bad_request(
                code="REASON_REQUIRED",
                detail="Cancellation reason is required (min 2 chars).",
            )

        stmt = (
            select(Token, Patient, Doctor)
            .join(Patient, Token.patient_id == Patient.id)
            .join(Doctor, Token.doctor_id == Doctor.id)
            .where(
                Token.id == token_id,
                Token.clinic_id == clinic_id,
            )
        )
        res = await self.session.execute(stmt)
        row = res.one_or_none()
        if not row:
            raise not_found(
                code="TOKEN_NOT_FOUND",
                detail=f"Token with ID {token_id} not found.",
            )

        token, patient, doctor = row

        if token.status in ("done", "cancelled"):
            raise conflict(
                code="CANNOT_CANCEL",
                detail=f"Token with status '{token.status}' cannot be cancelled.",
            )

        old_status = token.status
        token.status = "cancelled"
        token.cancelled_reason = reason.strip()

        token_event = TokenEvent(
            token_id=token.id,
            clinic_id=token.clinic_id,
            from_status=old_status,
            to_status="cancelled",
            actor_type="staff",
            actor_id=current_user.user_id,
        )
        self.session.add(token_event)

        AuditService.record_audit(
            session=self.session,
            action="token.cancel",
            entity="token",
            entity_id=token.id,
            actor_type="staff",
            actor_id=current_user.user_id,
            clinic_id=token.clinic_id,
            before={"status": old_status},
            after={"status": "cancelled", "reason": reason.strip()},
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()
        await self.session.refresh(token)

        try:
            realtime_client = SupabaseRealtimeClient()
            await realtime_client.broadcast_queue_update(
                clinic_id=token.clinic_id,
                doctor_id=token.doctor_id,
                event="token.cancelled",
                token_number=token.number,
                non_blocking=True,
            )
        except Exception as exc:
            logger.warning("Realtime broadcast skipped on cancel_token_by_staff: %s", exc)

        raw_phone = patient.phone or ""
        masked_phone = f"***{raw_phone[-4:]}" if len(raw_phone) >= 4 else "***"

        return ReceptionTokenListItem(
            id=token.id,
            number=token.number,
            patient_id=patient.id,
            patient_name=patient.name,
            phone=masked_phone,
            source=token.source,
            status=token.status,
            doctor_id=doctor.id,
            doctor_name=doctor.name,
            visit_date=token.visit_date,
            position=token.position,
            arrived_at=token.arrived_at,
            called_at=token.called_at,
            completed_at=token.completed_at,
            cancelled_reason=token.cancelled_reason,
            created_at=token.created_at,
        )
