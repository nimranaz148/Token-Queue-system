import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class DisplayPairInitiateRequest(BaseModel):
    device_name: Annotated[
        str, Field(min_length=2, max_length=100, description="e.g. Waiting Room TV")
    ]
    doctor_ids: Annotated[
        list[uuid.UUID], Field(min_length=1, max_length=4, description="1 to 4 doctors")
    ]


class DisplayPairInitiateResponse(BaseModel):
    pairing_code: str
    expires_at: datetime
    device_name: str


class DisplayPairCompleteRequest(BaseModel):
    pairing_code: Annotated[str, Field(min_length=6, max_length=10)]


class DisplayPairCompleteResponse(BaseModel):
    device_id: uuid.UUID
    device_token: str
    clinic_id: uuid.UUID
    clinic_name: str


class DisplayDeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    doctor_ids: list[str]
    paired_at: datetime
    revoked_at: datetime | None = None
    is_active: bool


class DisplayDoctorFeed(BaseModel):
    doctor_id: uuid.UUID
    doctor_name: str
    specialty: str | None = None
    current_token: int | None = None
    next_tokens: list[int] = []


class DisplayFeedResponse(BaseModel):
    clinic_name: str
    doctors: list[DisplayDoctorFeed]
    server_time: datetime
