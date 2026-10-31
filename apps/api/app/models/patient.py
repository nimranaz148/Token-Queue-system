from datetime import date

from sqlalchemy import Date, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel, SoftDeleteMixin, TenantMixin, TimestampMixin


class Patient(BaseModel, TenantMixin, SoftDeleteMixin, TimestampMixin):
    """Patient record registered at a clinic."""

    __tablename__ = "patients"
    __table_args__ = (Index("ix_patients_clinic_phone", "clinic_id", "phone"),)

    phone: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
