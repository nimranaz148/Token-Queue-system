import uuid
from datetime import time

from sqlalchemy import Boolean, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel, SoftDeleteMixin, TenantMixin, TimestampMixin


class Doctor(BaseModel, TenantMixin, SoftDeleteMixin, TimestampMixin):
    """Doctor practicing at a specific clinic."""

    __tablename__ = "doctors"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    specialty: Mapped[str | None] = mapped_column(String(255), nullable=True)
    daily_online_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    consult_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class DoctorSchedule(BaseModel, TenantMixin, TimestampMixin):
    """OPD schedule entry for a doctor on a specific weekday (0=Monday..6=Sunday)."""

    __tablename__ = "doctor_schedules"
    __table_args__ = (
        UniqueConstraint("doctor_id", "weekday", name="uq_doctor_schedules_doctor_weekday"),
    )

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
