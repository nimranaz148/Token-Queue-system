import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, BaseModel, TenantMixin, TimestampMixin


class Token(BaseModel, TenantMixin, TimestampMixin):
    """Queue token issued to a patient for an OPD visit on a specific date."""

    __tablename__ = "tokens"
    __table_args__ = (
        UniqueConstraint(
            "clinic_id",
            "doctor_id",
            "visit_date",
            "number",
            name="uq_tokens_clinic_doctor_date_number",
        ),
        Index(
            "ix_tokens_queue_position",
            "clinic_id",
            "doctor_id",
            "visit_date",
            "status",
            "position",
        ),
    )

    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    visit_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)  # online | walk_in
    status: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # booked, arrived, serving, etc.
    public_code: Mapped[str] = mapped_column(String(22), unique=True, index=True, nullable=False)
    estimated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    arrived_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    called_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_reason: Mapped[str | None] = mapped_column(Text, nullable=True)


class TokenCounter(Base):
    """Atomic token counter per doctor per day, locked during token issuance."""

    __tablename__ = "token_counters"
    __table_args__ = (PrimaryKeyConstraint("clinic_id", "doctor_id", "visit_date"),)

    clinic_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id", ondelete="CASCADE"),
        nullable=False,
    )
    doctor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
    )
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    last_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class TokenEvent(BaseModel, TenantMixin):
    """Immutable log of token state transitions for auditing and metrics."""

    __tablename__ = "token_events"

    token_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tokens.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_status: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_type: Mapped[str] = mapped_column(String(30), nullable=False)  # patient|staff|system|ai
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
