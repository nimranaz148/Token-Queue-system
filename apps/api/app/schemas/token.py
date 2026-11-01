import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TokenBookingRequest(BaseModel):
    """Payload for patient online token booking (PRD §5.3 F-001, W-001)."""

    doctor_id: uuid.UUID = Field(..., description="ID of the doctor / OPD selected")
    visit_date: date = Field(
        ..., description="Visit date ('today' or 'tomorrow' in clinic time zone)"
    )
    patient_name: str = Field(
        ...,
        min_length=2,
        max_length=60,
        description="Patient full name (2-60 characters)",
    )
    phone: str = Field(
        ...,
        min_length=7,
        max_length=50,
        description="Patient contact phone number",
    )
    turnstile_token: str = Field(
        ...,
        description="Cloudflare Turnstile verification challenge token",
    )


class TokenBookingResponse(BaseModel):
    """Response returned upon successful token issuance (PRD F-001, F-002)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    public_code: str
    status: str
    source: str
    visit_date: date
    doctor_id: uuid.UUID
    doctor_name: str
    clinic_name: str
    clinic_slug: str
    position: Decimal | float
    estimated_at: datetime | None = None
    created_at: datetime


class PublicDoctorSchedule(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    weekday: int
    start_time: str
    end_time: str


class PublicDoctorInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    specialty: str | None = None
    daily_online_limit: int | None = None
    consult_minutes: int | None = None
    schedules: list[PublicDoctorSchedule] = []


class PublicClinicInfoResponse(BaseModel):
    """Publicly accessible clinic profile for the booking screen."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    time_zone: str
    address: str | None = None
    phone: str | None = None
    online_booking_enabled: bool = True
    doctors: list[PublicDoctorInfo] = []


class TokenDetailsResponse(BaseModel):
    """Detailed token state for Token Confirm (F-002) and Live Queue (F-003)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    public_code: str
    status: str
    source: str
    visit_date: date
    doctor_id: uuid.UUID
    doctor_name: str
    specialty: str | None = None
    clinic_id: uuid.UUID
    clinic_name: str
    clinic_slug: str
    position: Decimal | float
    estimated_at: datetime | None = None
    people_ahead: int = 0
    estimated_wait_minutes: int = 0
    current_serving_number: int | None = None
    cancelled_reason: str | None = None
    created_at: datetime


class TokenCancelResponse(BaseModel):
    """Response returned when a token is cancelled."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    public_code: str
    status: str
    cancelled_reason: str | None = None
    message: str = "Token cancelled successfully."


class ReceptionTokenListItem(BaseModel):
    """Row item in Aaj ki List reception view (PRD §5.3 F-004)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    patient_id: uuid.UUID
    patient_name: str
    phone: str
    source: str
    status: str
    doctor_id: uuid.UUID
    doctor_name: str
    visit_date: date
    position: Decimal | float
    arrived_at: datetime | None = None
    called_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_reason: str | None = None
    created_at: datetime


class ReceptionTokenListResponse(BaseModel):
    """Paginated response for Aaj ki List (PRD §5.3 F-004)."""

    items: list[ReceptionTokenListItem]
    total: int
    date: date


class TokenCancelStaffRequest(BaseModel):
    """Payload for staff cancellation of a token with required reason (PRD §5.3 F-004)."""

    reason: str = Field(..., min_length=2, max_length=200, description="Reason required")


class WalkInTokenCreateRequest(BaseModel):
    """Payload for Walk-in Entry at reception (PRD §5.3 F-005)."""

    doctor_id: uuid.UUID = Field(..., description="Active doctor with OPD today")
    patient_name: str = Field(..., min_length=2, max_length=60, description="2-60 chars")
    phone: str = Field(..., min_length=7, max_length=50, description="E.164 phone number")
    existing_patient_id: uuid.UUID | None = Field(
        default=None, description="Set when picked from autocomplete"
    )
    ignore_daily_limit: bool = Field(
        default=False, description="Owner/reception may exceed daily limit; audited"
    )


class WalkInTokenResponse(BaseModel):
    """Response returned upon walk-in token creation (PRD §5.3 F-005)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    public_code: str
    status: str
    source: str
    patient_id: uuid.UUID
    patient_name: str
    phone: str
    doctor_id: uuid.UUID
    doctor_name: str
    visit_date: date
    position: Decimal | float
    arrived_at: datetime
    created_at: datetime


class DoctorQueueToken(BaseModel):
    """Token representation in the doctor consultation panel (PRD §5.3 F-007)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    number: int
    public_code: str
    status: str
    source: str
    patient_id: uuid.UUID
    patient_name: str
    patient_age: int | None = None
    patient_gender: str | None = None
    position: Decimal | float
    arrived_at: datetime | None = None
    called_at: datetime | None = None
    cancelled_reason: str | None = None
    created_at: datetime


class DoctorQueueResponse(BaseModel):
    """Active queue snapshot for doctor panel (PRD §5.3 F-007)."""

    doctor_id: uuid.UUID
    doctor_name: str
    visit_date: date
    current_token: DoctorQueueToken | None = None
    next_tokens: list[DoctorQueueToken] = []
    waiting_tokens: list[DoctorQueueToken] = []
    skipped_tokens: list[DoctorQueueToken] = []
    counts: dict[str, int] = {}


class DoctorNextActionRequest(BaseModel):
    """Payload to advance doctor queue to the next patient (PRD §5.3 F-007, W-004)."""

    doctor_id: uuid.UUID | None = None
    quick_note: str | None = Field(None, max_length=2000)


class DoctorSkipActionRequest(BaseModel):
    """Payload to mark current patient as skipped (PRD §5.3 F-007, W-004)."""

    doctor_id: uuid.UUID | None = None


class DoctorHoldActionRequest(BaseModel):
    """Payload to mark current patient on hold (PRD §5.3 F-007, W-004)."""

    doctor_id: uuid.UUID | None = None
    reason: str | None = Field(None, max_length=200)


class DoctorRecallActionRequest(BaseModel):
    """Payload to recall a skipped or hold patient to the front of queue (PRD §5.3 F-007)."""

    token_id: uuid.UUID
    doctor_id: uuid.UUID | None = None


class DoctorNextActionResponse(BaseModel):
    """Result of NEXT / skip / hold / recall queue action (PRD §5.3 F-007)."""

    success: bool = True
    previous_token: DoctorQueueToken | None = None
    current_token: DoctorQueueToken | None = None
    already_advanced: bool = False
    message: str


class SharedVisitAdviceResponse(BaseModel):
    """Doctor ki Hidayat patient prescription report (PRD §5.3 F-021)."""

    shared: bool
    public_code: str
    token_number: int | None = None
    visit_date: date | None = None
    doctor_name: str | None = None
    medicines_advice: str | None = None
    message: str | None = None
