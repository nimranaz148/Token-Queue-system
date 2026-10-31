import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseModel, TimestampMixin


class Clinic(BaseModel, TimestampMixin):
    """Clinic entity representing a tenant organization."""

    __tablename__ = "clinics"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="trial", nullable=False)
    time_zone: Mapped[str] = mapped_column(String(50), default="Asia/Karachi", nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    maps_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_path: Mapped[str | None] = mapped_column(String(255), nullable=True)


class ClinicSettings(Base):
    """Operational settings and configuration per clinic."""

    __tablename__ = "clinic_settings"

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        primary_key=True,
    )
    online_booking_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    daily_online_limit: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    advance_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    default_consult_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    call_only_arrived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    language_default: Mapped[str] = mapped_column(String(20), default="en", nullable=False)
    share_advice_with_patient: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_notes_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_consent_accepted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    ai_consent_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        onupdate=lambda: datetime.now(UTC),
    )
