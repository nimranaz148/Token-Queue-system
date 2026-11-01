import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class VisitListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    doctor_id: uuid.UUID
    doctor_name: str
    complaint: str | None = None
    notes: str | None = None
    medicines_advice: str | None = None
    share_with_patient: bool = True
    token_id: uuid.UUID | None = None
    token_number: int | None = None
    created_at: datetime


class PatientHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: uuid.UUID
    patient_name: str
    phone: str
    date_of_birth: date | None = None
    gender: str | None = None
    notes: str | None = None
    share_advice_clinic_setting: bool = False
    visits: list[VisitListItem] = []


class VisitCreateRequest(BaseModel):
    patient_id: uuid.UUID
    token_id: uuid.UUID | None = None
    complaint: Annotated[str | None, Field(default=None, max_length=500)] = None
    notes: Annotated[str | None, Field(default=None, max_length=4000)] = None
    medicines_advice: Annotated[str | None, Field(default=None, max_length=2000)] = None
    share_with_patient: bool = True


class VisitUpdateRequest(BaseModel):
    complaint: Annotated[str | None, Field(default=None, max_length=500)] = None
    notes: Annotated[str | None, Field(default=None, max_length=4000)] = None
    medicines_advice: Annotated[str | None, Field(default=None, max_length=2000)] = None
    share_with_patient: bool = True
