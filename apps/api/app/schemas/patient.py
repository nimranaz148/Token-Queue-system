import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.phone import normalize_phone


class PatientSearchResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    phone: str
    date_of_birth: date | None = None
    gender: str | None = None
    visit_count: int = 0
    last_visit_date: date | None = None


class PatientDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    name: str
    phone: str
    date_of_birth: date | None = None
    gender: str | None = None
    notes: str | None = None
    visit_count: int = 0
    last_visit_date: date | None = None
    created_at: datetime
    updated_at: datetime | None = None


class PatientUpdateRequest(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=60)]
    phone: Annotated[str, Field(min_length=7, max_length=20)]
    date_of_birth: date | None = None
    gender: Annotated[str | None, Field(default=None, max_length=20)] = None
    notes: Annotated[str | None, Field(default=None, max_length=4000)] = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        return normalize_phone(v)

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date | None) -> date | None:
        if v is not None and v > date.today():
            raise ValueError("Date of birth must be in the past")
        return v
