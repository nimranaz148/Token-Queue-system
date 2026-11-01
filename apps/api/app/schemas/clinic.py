import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


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
    clinic_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=80,
        description="Alias for clinic name per PRD §5.3 F-013",
    )
    owner_name: str = Field(
        default="Clinic Owner",
        min_length=2,
        max_length=100,
        description="Full name of clinic owner",
    )
    owner_email: EmailStr = Field(
        default="owner@example.com",
        description="Email of clinic owner for magic link invitation",
    )
    owner_phone: str | None = Field(
        default=None,
        max_length=50,
        description="Owner contact phone (+92 E.164 format)",
    )
    status: str = Field(
        default="trial",
        description="Initial clinic status: trial, active, or suspended",
    )

    @field_validator("status")
    @classmethod
    def validate_initial_status(cls, v: str) -> str:
        valid_statuses = {"trial", "active", "suspended"}
        if v not in valid_statuses:
            raise ValueError(f"Invalid status '{v}'. Allowed: {valid_statuses}")
        return v

    @model_validator(mode="before")
    @classmethod
    def sync_name_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "clinic_name" in data and not data.get("name"):
                data["name"] = data["clinic_name"]
            elif "name" in data and not data.get("clinic_name"):
                data["clinic_name"] = data["name"]
        return data


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
    owner_name: str | None = None
    owner_email: str | None = None
    owner_phone: str | None = None
    doctors_count: int = Field(default=0, description="Active doctors count in clinic")
    tokens_last_7d: int = Field(default=0, description="Tokens generated in last 7 days")
    created_at: datetime




class ClinicListResponse(BaseModel):
    items: list[ClinicResponse]
    total: int
