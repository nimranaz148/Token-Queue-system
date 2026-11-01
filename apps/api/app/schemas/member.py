import uuid
from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class MemberRole(StrEnum):
    OWNER = "owner"
    DOCTOR = "doctor"
    RECEPTION = "reception"


class MemberInviteRequest(BaseModel):
    name: Annotated[
        str, Field(min_length=2, max_length=255, description="Full name of staff member")
    ]
    email: Annotated[EmailStr, Field(description="Unique email address for staff login")]
    phone: Annotated[
        str | None,
        Field(default=None, max_length=50, description="Contact phone in E.164 or local format"),
    ]
    role: Annotated[MemberRole, Field(description="Role: owner, doctor, or reception")]
    doctor_id: Annotated[
        uuid.UUID | None,
        Field(default=None, description="Linked doctor ID (required if role is doctor)"),
    ]


class MemberUpdateRequest(BaseModel):
    name: Annotated[str | None, Field(default=None, min_length=2, max_length=255)]
    phone: Annotated[str | None, Field(default=None, max_length=50)]
    role: Annotated[MemberRole | None, Field(default=None)]
    doctor_id: Annotated[uuid.UUID | None, Field(default=None)]
    active: Annotated[bool | None, Field(default=None)]


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    email: str
    phone: str | None = None
    role: str
    doctor_id: uuid.UUID | None = None
    doctor_name: str | None = None
    active: bool
    created_at: datetime
    updated_at: datetime


class MemberListResponse(BaseModel):
    items: list[MemberResponse]
    total: int
