import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditAction(StrEnum):
    """Enumeration of all audited security and domain operations required by PRD §14.1."""

    # Token actions
    TOKEN_CREATE = "token.create"
    TOKEN_ARRIVE = "token.arrive"
    TOKEN_CANCEL = "token.cancel"
    TOKEN_NEXT = "token.next"
    TOKEN_SKIP = "token.skip"
    TOKEN_HOLD = "token.hold"
    TOKEN_RECALL = "token.recall"
    TOKEN_NO_SHOW = "token.no_show"
    WALK_IN_OVER_LIMIT = "token.walk_in_over_limit"

    # Patient actions
    PATIENT_CREATE = "patient.create"
    PATIENT_EDIT = "patient.edit"
    PATIENT_MERGE = "patient.merge"

    # Visit actions
    VISIT_CREATE = "visit.create"
    VISIT_EDIT = "visit.edit"
    PATIENT_VIEW_SHARED_ADVICE = "visit.patient_view_shared_advice"

    # Settings actions
    SETTINGS_CHANGE = "settings.change"

    # Doctor and schedule actions
    DOCTOR_CHANGE = "doctor.change"
    SCHEDULE_CHANGE = "schedule.change"

    # Member actions
    MEMBER_INVITE = "member.invite"
    MEMBER_ROLE_CHANGE = "member.role_change"
    MEMBER_DEACTIVATE = "member.deactivate"

    # Display device actions
    DISPLAY_PAIR = "display.pair"
    DISPLAY_REVOKE = "display.revoke"

    # Clinic lifecycle actions
    CLINIC_CREATE = "clinic.create"
    CLINIC_STATUS_CHANGE = "clinic.status_change"

    # Data export action
    DATA_EXPORT = "data.export"

    # Authentication actions
    LOGIN_SUCCESS = "login.success"
    LOGIN_FAILURE = "login.failure"

    # AI run action
    AI_RUN = "ai.run"


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID | None = None
    actor_type: str
    actor_id: uuid.UUID | None = None
    action: str
    entity: str
    entity_id: uuid.UUID | None = None
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    request_id: str | None = None
    ip_hash: str | None = None
    at: datetime
