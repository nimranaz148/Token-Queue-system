import logging
import uuid
from datetime import UTC, datetime, time

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import not_found
from app.models.doctor import Doctor, DoctorSchedule
from app.schemas.doctor import (
    DoctorCreate,
    DoctorResponse,
    DoctorScheduleCreate,
    DoctorScheduleResponse,
    DoctorUpdate,
)
from app.services.audit import AuditService

logger = logging.getLogger(__name__)


class DoctorService:
    """Domain service managing doctor profiles and OPD schedules (PRD §5.3 F-016)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_doctors(
        self,
        clinic_id: uuid.UUID,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[DoctorResponse], int]:
        """List doctors belonging to the specified clinic tenant with pagination."""
        base_filter = [
            Doctor.clinic_id == clinic_id,
            Doctor.deleted_at.is_(None),
        ]
        if active_only:
            base_filter.append(Doctor.active.is_(True))

        # Total count query
        count_stmt = select(func.count(Doctor.id)).where(*base_filter)
        count_res = await self.session.execute(count_stmt)
        total = count_res.scalar() or 0

        # Paginated items query
        stmt = select(Doctor).where(*base_filter).order_by(Doctor.name).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        doctors = res.scalars().all()

        results: list[DoctorResponse] = []
        for doc in doctors:
            sched_stmt = (
                select(DoctorSchedule)
                .where(
                    DoctorSchedule.clinic_id == clinic_id,
                    DoctorSchedule.doctor_id == doc.id,
                )
                .order_by(DoctorSchedule.weekday, DoctorSchedule.start_time)
            )
            sched_res = await self.session.execute(sched_stmt)
            schedules = sched_res.scalars().all()

            results.append(
                DoctorResponse(
                    id=doc.id,
                    clinic_id=doc.clinic_id,
                    name=doc.name,
                    specialty=doc.specialty,
                    daily_online_limit=doc.daily_online_limit,
                    consult_minutes=doc.consult_minutes,
                    active=doc.active,
                    schedules=[
                        DoctorScheduleResponse(
                            id=s.id,
                            doctor_id=s.doctor_id,
                            weekday=s.weekday,
                            start_time=s.start_time.strftime("%H:%M"),
                            end_time=s.end_time.strftime("%H:%M"),
                        )
                        for s in schedules
                    ],
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                )
            )

        return results, total

    async def get_doctor(self, clinic_id: uuid.UUID, doctor_id: uuid.UUID) -> DoctorResponse:
        """Fetch a specific doctor by ID, strictly scoped to caller's clinic."""
        stmt = select(Doctor).where(
            Doctor.id == doctor_id,
            Doctor.clinic_id == clinic_id,
            Doctor.deleted_at.is_(None),
        )
        res = await self.session.execute(stmt)
        doc = res.scalar_one_or_none()
        if not doc:
            raise not_found(code="DOCTOR_NOT_FOUND", detail="Doctor not found in this clinic.")

        sched_stmt = (
            select(DoctorSchedule)
            .where(
                DoctorSchedule.clinic_id == clinic_id,
                DoctorSchedule.doctor_id == doc.id,
            )
            .order_by(DoctorSchedule.weekday, DoctorSchedule.start_time)
        )
        sched_res = await self.session.execute(sched_stmt)
        schedules = sched_res.scalars().all()

        return DoctorResponse(
            id=doc.id,
            clinic_id=doc.clinic_id,
            name=doc.name,
            specialty=doc.specialty,
            daily_online_limit=doc.daily_online_limit,
            consult_minutes=doc.consult_minutes,
            active=doc.active,
            schedules=[
                DoctorScheduleResponse(
                    id=s.id,
                    doctor_id=s.doctor_id,
                    weekday=s.weekday,
                    start_time=s.start_time.strftime("%H:%M"),
                    end_time=s.end_time.strftime("%H:%M"),
                )
                for s in schedules
            ],
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

    async def create_doctor(
        self,
        clinic_id: uuid.UUID,
        data: DoctorCreate,
        actor_id: uuid.UUID,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> DoctorResponse:
        """Register a new doctor for this clinic tenant with optional initial schedules."""
        now = datetime.now(UTC)
        doctor = Doctor(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            name=data.name.strip(),
            specialty=data.specialty.strip() if data.specialty else None,
            daily_online_limit=data.daily_online_limit,
            consult_minutes=data.consult_minutes,
            active=data.active,
            created_at=now,
            updated_at=now,
        )
        self.session.add(doctor)
        await self.session.flush()

        saved_schedules: list[DoctorSchedule] = []
        for s in data.schedules:
            start_parts = [int(p) for p in s.start_time.split(":")]
            end_parts = [int(p) for p in s.end_time.split(":")]
            sched = DoctorSchedule(
                id=uuid.uuid4(),
                clinic_id=clinic_id,
                doctor_id=doctor.id,
                weekday=s.weekday,
                start_time=time(start_parts[0], start_parts[1]),
                end_time=time(end_parts[0], end_parts[1]),
                created_at=now,
                updated_at=now,
            )
            self.session.add(sched)
            saved_schedules.append(sched)

        # Audit row
        AuditService.record_audit(
            session=self.session,
            action="doctor.change",
            entity="doctor",
            entity_id=doctor.id,
            actor_type="owner",
            actor_id=actor_id,
            clinic_id=clinic_id,
            after={
                "name": doctor.name,
                "specialty": doctor.specialty,
                "active": doctor.active,
                "daily_online_limit": doctor.daily_online_limit,
                "consult_minutes": doctor.consult_minutes,
                "schedule_count": len(saved_schedules),
            },
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()
        await self.session.refresh(doctor)

        return DoctorResponse(
            id=doctor.id,
            clinic_id=doctor.clinic_id,
            name=doctor.name,
            specialty=doctor.specialty,
            daily_online_limit=doctor.daily_online_limit,
            consult_minutes=doctor.consult_minutes,
            active=doctor.active,
            schedules=[
                DoctorScheduleResponse(
                    id=s.id,
                    doctor_id=s.doctor_id,
                    weekday=s.weekday,
                    start_time=s.start_time.strftime("%H:%M"),
                    end_time=s.end_time.strftime("%H:%M"),
                )
                for s in saved_schedules
            ],
            created_at=doctor.created_at,
            updated_at=doctor.updated_at,
        )

    async def update_doctor(
        self,
        clinic_id: uuid.UUID,
        doctor_id: uuid.UUID,
        data: DoctorUpdate,
        actor_id: uuid.UUID,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> DoctorResponse:
        """Update doctor settings (active, limits, specialty)."""
        stmt = select(Doctor).where(
            Doctor.id == doctor_id,
            Doctor.clinic_id == clinic_id,
            Doctor.deleted_at.is_(None),
        )
        res = await self.session.execute(stmt)
        doctor = res.scalar_one_or_none()
        if not doctor:
            raise not_found(code="DOCTOR_NOT_FOUND", detail="Doctor not found in this clinic.")

        before = {
            "name": doctor.name,
            "specialty": doctor.specialty,
            "active": doctor.active,
            "daily_online_limit": doctor.daily_online_limit,
            "consult_minutes": doctor.consult_minutes,
        }

        if data.name is not None:
            doctor.name = data.name.strip()
        if data.specialty is not None:
            doctor.specialty = data.specialty.strip() if data.specialty else None
        if data.daily_online_limit is not None:
            doctor.daily_online_limit = data.daily_online_limit
        if data.consult_minutes is not None:
            doctor.consult_minutes = data.consult_minutes
        if data.active is not None:
            doctor.active = data.active

        doctor.updated_at = datetime.now(UTC)

        AuditService.record_audit(
            session=self.session,
            action="doctor.change",
            entity="doctor",
            entity_id=doctor.id,
            actor_type="owner",
            actor_id=actor_id,
            clinic_id=clinic_id,
            before=before,
            after={
                "name": doctor.name,
                "specialty": doctor.specialty,
                "active": doctor.active,
                "daily_online_limit": doctor.daily_online_limit,
                "consult_minutes": doctor.consult_minutes,
            },
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()
        await self.session.refresh(doctor)

        return await self.get_doctor(clinic_id=clinic_id, doctor_id=doctor.id)

    async def update_schedules(
        self,
        clinic_id: uuid.UUID,
        doctor_id: uuid.UUID,
        schedules: list[DoctorScheduleCreate],
        actor_id: uuid.UUID,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> list[DoctorScheduleResponse]:
        """Replace all weekly OPD schedules for a doctor."""
        stmt = select(Doctor).where(
            Doctor.id == doctor_id,
            Doctor.clinic_id == clinic_id,
            Doctor.deleted_at.is_(None),
        )
        res = await self.session.execute(stmt)
        doctor = res.scalar_one_or_none()
        if not doctor:
            raise not_found(code="DOCTOR_NOT_FOUND", detail="Doctor not found in this clinic.")

        # Delete existing schedules
        del_stmt = delete(DoctorSchedule).where(
            DoctorSchedule.clinic_id == clinic_id,
            DoctorSchedule.doctor_id == doctor_id,
        )
        await self.session.execute(del_stmt)

        now = datetime.now(UTC)
        saved_schedules: list[DoctorSchedule] = []
        for s in schedules:
            start_parts = [int(p) for p in s.start_time.split(":")]
            end_parts = [int(p) for p in s.end_time.split(":")]
            sched = DoctorSchedule(
                id=uuid.uuid4(),
                clinic_id=clinic_id,
                doctor_id=doctor.id,
                weekday=s.weekday,
                start_time=time(start_parts[0], start_parts[1]),
                end_time=time(end_parts[0], end_parts[1]),
                created_at=now,
                updated_at=now,
            )
            self.session.add(sched)
            saved_schedules.append(sched)

        AuditService.record_audit(
            session=self.session,
            action="schedule.change",
            entity="doctor_schedule",
            entity_id=doctor.id,
            actor_type="owner",
            actor_id=actor_id,
            clinic_id=clinic_id,
            after={"doctor_id": str(doctor.id), "schedule_count": len(saved_schedules)},
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()

        return [
            DoctorScheduleResponse(
                id=s.id,
                doctor_id=s.doctor_id,
                weekday=s.weekday,
                start_time=s.start_time.strftime("%H:%M"),
                end_time=s.end_time.strftime("%H:%M"),
            )
            for s in saved_schedules
        ]

    async def delete_doctor(
        self,
        clinic_id: uuid.UUID,
        doctor_id: uuid.UUID,
        actor_id: uuid.UUID,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> None:
        """Soft-delete a doctor and deactivate them from online queue bookings."""
        stmt = select(Doctor).where(
            Doctor.id == doctor_id,
            Doctor.clinic_id == clinic_id,
            Doctor.deleted_at.is_(None),
        )
        res = await self.session.execute(stmt)
        doctor = res.scalar_one_or_none()
        if not doctor:
            raise not_found(code="DOCTOR_NOT_FOUND", detail="Doctor not found in this clinic.")

        doctor.deleted_at = datetime.now(UTC)
        doctor.active = False
        doctor.updated_at = datetime.now(UTC)

        AuditService.record_audit(
            session=self.session,
            action="doctor.change",
            entity="doctor",
            entity_id=doctor.id,
            actor_type="owner",
            actor_id=actor_id,
            clinic_id=clinic_id,
            after={"action": "soft_deleted", "active": False},
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()
