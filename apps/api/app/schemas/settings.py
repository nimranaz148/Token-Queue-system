import datetime as dt
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClinicSettingsRead(BaseModel):
    """Full clinic operational settings per PRD §5.3 F-011."""

    model_config = ConfigDict(from_attributes=True)

    clinic_id: uuid.UUID
    clinic_name: str
    slug: str
    time_zone: str = "Asia/Karachi"
    address: str | None = None
    phone: str | None = None
    maps_url: str | None = None
    logo_path: str | None = None

    online_booking_enabled: bool = True
    daily_online_limit: int = Field(default=50, ge=1, le=500)
    advance_days: int = Field(default=1, ge=0, le=1)
    default_consult_minutes: int = Field(default=10, ge=2, le=60)
    call_only_arrived: bool = False
    language_default: str = "en"
    share_advice_with_patient: bool = False
    ai_notes_enabled: bool = False
    ai_consent_accepted_by: uuid.UUID | None = None
    ai_consent_accepted_at: dt.datetime | None = None
    version: int = 1
    updated_at: dt.datetime


class ClinicSettingsUpdate(BaseModel):
    """Payload to update clinic settings with optimistic concurrency version check."""

    version: int = Field(..., description="Current version of the settings for optimistic locking")

    # Clinic profile fields
    clinic_name: str | None = Field(default=None, min_length=2, max_length=80)
    time_zone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)
    maps_url: str | None = Field(default=None, max_length=500)
    logo_path: str | None = Field(default=None, max_length=255)

    # Operational settings
    online_booking_enabled: bool | None = None
    daily_online_limit: int | None = Field(default=None, ge=1, le=500)
    advance_days: int | None = Field(default=None, ge=0, le=1)
    default_consult_minutes: int | None = Field(default=None, ge=2, le=60)
    call_only_arrived: bool | None = None
    language_default: str | None = None
    share_advice_with_patient: bool | None = None
    ai_notes_enabled: bool | None = None

    @field_validator("language_default")
    @classmethod
    def validate_language(cls, v: str | None) -> str | None:
        if v is not None and v not in {"en", "roman_ur"}:
            raise ValueError("language_default must be 'en' or 'roman_ur'")
        return v
