import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class DailyReportKPIs(BaseModel):
    """Core KPI metrics for Roz ki Report (PRD §5.3 F-010 / §29.1 D-001)."""

    patients_seen: int = Field(default=0, description="Total patients marked done")
    avg_wait_minutes: Decimal | None = Field(
        default=None, description="Average wait duration in minutes"
    )
    no_shows: int = Field(default=0, description="Tokens expired or marked no-show")
    online_share_pct: Decimal = Field(
        default=Decimal("0.0"), description="Percentage of tokens booked online (0-100)"
    )
    total_tokens: int = Field(default=0, description="Total tokens issued today")
    online_count: int = Field(default=0, description="Tokens booked via online link")
    walk_in_count: int = Field(default=0, description="Tokens issued at reception")
    cancelled_count: int = Field(default=0, description="Tokens cancelled before serving")


class DailyTrendItem(BaseModel):
    """Daily metric item for 7-day trend chart."""

    date: dt.date
    day_name: str
    patients_seen: int
    no_shows: int
    total_tokens: int


class DailyReportResponse(BaseModel):
    """Full Roz ki Report payload returned by GET /api/v1/reports/daily."""

    model_config = ConfigDict(from_attributes=True)

    clinic_id: uuid.UUID
    date: dt.date
    doctor_id: uuid.UUID | None = None
    doctor_name: str | None = None
    kpis: DailyReportKPIs
    trend_7_days: list[DailyTrendItem]
