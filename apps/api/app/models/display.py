from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel, TenantMixin, TimestampMixin


class DisplayDevice(BaseModel, TenantMixin, TimestampMixin):
    """Waiting room TV display paired to one or more clinic doctors."""

    __tablename__ = "display_devices"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    doctor_ids: Mapped[list[Any]] = mapped_column(JSONB, default=list, nullable=False)
    paired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
