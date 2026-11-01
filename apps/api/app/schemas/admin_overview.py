import datetime as dt
import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PlatformKPIs(BaseModel):
    """Platform-wide operational KPIs for D-002 Platform Overview."""

    active_clinics: int = Field(default=0, description="Total clinics with status 'active'")
    total_clinics: int = Field(default=0, description="Total registered clinics on platform")
    tokens_today: int = Field(default=0, description="Total tokens issued platform-wide today")
    tokens_7_days: int = Field(
        default=0, description="Total tokens issued platform-wide in last 7 days"
    )
    idle_clinics: int = Field(
        default=0, description="Clinics with zero token activity in last 3+ days"
    )
    ai_spend_this_month: Decimal = Field(
        default=Decimal("0.00"), description="Total inference spend in USD this calendar month"
    )


class ClinicOverviewItem(BaseModel):
    """Clinic status and telemetry summary row in Platform Overview table."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    status: str
    tokens_7d: int = 0
    tokens_today: int = 0
    last_activity: dt.datetime | None = None


class PlatformOverviewResponse(BaseModel):
    """Response payload for GET /api/v1/admin/overview (PRD §29.2 D-002)."""

    kpis: PlatformKPIs
    clinics: list[ClinicOverviewItem]
