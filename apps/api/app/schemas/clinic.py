import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ClinicBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80, description="Clinic name")
    slug: str = Field(..., min_length=3, max_length=40, description="URL-friendly clinic slug")
    time_zone: str = Field(default="Asia/Karachi", max_length=50)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError("Slug must contain only lowercase alphanumeric characters and hyphens")
        return v.lower()


class ClinicCreate(ClinicBase):
    pass


class ClinicUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    address: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=50)


class ClinicStatusUpdate(BaseModel):
    status: str = Field(..., description="Target status: trial, active, or suspended")
    reason: str = Field(..., min_length=3, max_length=255, description="Audited reason for status change")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        valid_statuses = {"trial", "active", "suspended"}
        if v not in valid_statuses:
            raise ValueError(f"Invalid status '{v}'. Allowed: {valid_statuses}")
        return v


class ClinicResponse(ClinicBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    created_at: datetime


class ClinicListResponse(BaseModel):
    items: list[ClinicResponse]
    total: int
