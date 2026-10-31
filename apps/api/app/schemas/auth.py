import uuid
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Role(StrEnum):
    PLATFORM_ADMIN = "platform_admin"
    OWNER = "owner"
    DOCTOR = "doctor"
    RECEPTION = "reception"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str | None = Field(
        default=None, description="Password for email/password or dev auth"
    )
    clinic_id: uuid.UUID | None = Field(
        default=None, description="Clinic ID if member belongs to multiple clinics"
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token lifespan in seconds")
    refresh_token: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class CurrentUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: str
    name: str
    role: str
    clinic_id: uuid.UUID | None = None
    doctor_id: uuid.UUID | None = None
    is_platform_admin: bool = False


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: str
    name: str
    role: str
    clinic_id: uuid.UUID | None = None
    doctor_id: uuid.UUID | None = None
    is_platform_admin: bool
