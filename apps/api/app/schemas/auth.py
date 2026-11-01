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


class MagicLinkRequest(BaseModel):
    email: EmailStr = Field(description="Staff member or platform admin email address")


class MagicLinkResponse(BaseModel):
    message: str = Field(
        default="Login link email kar diya",
        description="Unified confirmation message shown for all requests (anti-enumeration)",
    )
    success: bool = True
    magic_link: str | None = Field(
        default=None,
        description="Magic login link/token for non-production environments to aid automated testing",
    )


class ClinicMembershipItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    clinic_id: uuid.UUID
    clinic_name: str
    role: str


class StaffMembershipsResponse(BaseModel):
    email: str
    memberships: list[ClinicMembershipItem] = Field(default_factory=list)


class SwitchClinicRequest(BaseModel):
    clinic_id: uuid.UUID = Field(description="Target clinic ID to switch active context to")

