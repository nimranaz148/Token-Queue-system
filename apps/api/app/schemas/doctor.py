import uuid
from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DoctorScheduleBase(BaseModel):
    weekday: int = Field(..., ge=0, le=6, description="Weekday (0=Monday..6=Sunday)")
    start_time: str = Field(..., description="Start time in HH:MM format")
    end_time: str = Field(..., description="End time in HH:MM format")

    @model_validator(mode="after")
    def validate_times(self) -> "DoctorScheduleBase":
        try:
            start_parts = [int(p) for p in self.start_time.split(":")]
            end_parts = [int(p) for p in self.end_time.split(":")]
            t_start = time(start_parts[0], start_parts[1])
            t_end = time(end_parts[0], end_parts[1])
        except Exception:
            raise ValueError("Time must be in valid HH:MM format") from None

        if t_end <= t_start:
            raise ValueError("End time must be after start time")
        return self


class DoctorScheduleCreate(DoctorScheduleBase):
    pass


class DoctorScheduleResponse(DoctorScheduleBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doctor_id: uuid.UUID


class DoctorCreate(BaseModel):
    """Payload to register a new doctor (PRD §5.3 F-016)."""

    name: str = Field(..., min_length=2, max_length=100, description="Doctor full name")
    specialty: str | None = Field(default=None, max_length=100, description="Medical specialty")
    daily_online_limit: int | None = Field(
        default=None,
        ge=1,
        le=500,
        description="Daily online booking limit override",
    )
    consult_minutes: int | None = Field(
        default=10,
        ge=5,
        le=60,
        description="Average consult duration in minutes (5..60)",
    )
    active: bool = Field(default=True, description="Whether doctor is active for OPD bookings")
    schedules: list[DoctorScheduleCreate] = Field(
        default=[], description="Initial weekly OPD schedules"
    )


class DoctorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    specialty: str | None = Field(default=None, max_length=100)
    daily_online_limit: int | None = Field(default=None, ge=1, le=500)
    consult_minutes: int | None = Field(default=None, ge=5, le=60)
    active: bool | None = Field(default=None)


class DoctorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    name: str
    specialty: str | None = None
    daily_online_limit: int | None = None
    consult_minutes: int | None = None
    active: bool
    schedules: list[DoctorScheduleResponse] = []
    created_at: datetime
    updated_at: datetime


class DoctorListResponse(BaseModel):
    items: list[DoctorResponse]
    total: int
