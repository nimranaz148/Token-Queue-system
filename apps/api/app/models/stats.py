import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel, TenantMixin, TimestampMixin


class DailyStats(BaseModel, TenantMixin, TimestampMixin):
    """Aggregated daily OPD queue performance metrics per doctor."""

    __tablename__ = "daily_stats"
    __table_args__ = (
        UniqueConstraint(
            "clinic_id", "doctor_id", "date", name="uq_daily_stats_clinic_doctor_date"
        ),
    )

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    seen: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    no_shows: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cancelled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    online_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    walk_in_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_wait_minutes: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    avg_consult_minutes: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
