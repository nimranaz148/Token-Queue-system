import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DayCloseRequest(BaseModel):
    """Payload for triggering the Day Close background job (W-006)."""

    clinic_id: uuid.UUID | None = Field(
        default=None, description="Optional clinic to close specifically."
    )
    date: dt.date | None = Field(
        default=None,
        description="Target visit date to close (defaults to today in clinic local time).",
    )
    force: bool = Field(
        default=False,
        description="Force run even if OPD end + 60 min has not passed.",
    )


class DoctorStatsSummary(BaseModel):
    """KPI summary written to daily_stats for a doctor on a given day."""

    model_config = ConfigDict(from_attributes=True)

    doctor_id: uuid.UUID
    seen: int
    no_shows: int
    cancelled: int
    online_count: int
    walk_in_count: int
    avg_wait_minutes: Decimal | None = None
    avg_consult_minutes: Decimal | None = None


class ClinicDayCloseResult(BaseModel):
    """Result of day close execution for a single clinic."""

    clinic_id: uuid.UUID
    clinic_name: str
    date: dt.date
    tokens_no_show: int
    tokens_done: int
    doctor_stats: list[DoctorStatsSummary]


class DayCloseResponse(BaseModel):
    """Response returned by POST /jobs/day-close."""

    success: bool
    processed_count: int
    results: list[ClinicDayCloseResult]


class DailyBriefJobRequest(BaseModel):
    """Payload for triggering the Daily Brief background job (W-010)."""

    clinic_id: uuid.UUID | None = Field(
        default=None, description="Optional clinic to generate brief for."
    )
    date: dt.date | None = Field(
        default=None, description="Target date for the brief (defaults to today)."
    )


class DailyBriefJobResponse(BaseModel):
    """Response returned by POST /jobs/daily-brief."""

    success: bool
    date: dt.date
    clinics_processed: int
    briefs_generated: int
    errors: list[str] = Field(default_factory=list)

