import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AIRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID | None = None
    feature: str
    requested_by: uuid.UUID | None = None
    provider: str
    model: str
    tools_called: list[Any] | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: Decimal = Field(default=Decimal("0.000000"))
    status: str
    error: str | None = None
    at: dt.datetime


class AIActivityResponse(BaseModel):
    items: list[AIRunRead]
    total: int


class AIBriefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clinic_id: uuid.UUID
    date: dt.date
    body_md: str
    anomalies: list[Any] | None = None
    feedback: str | None = None
    created_at: dt.datetime


class AIBriefFeedbackRequest(BaseModel):
    feedback: str = Field(..., pattern="^(up|down)$")


class PatientChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    at: dt.datetime


class PatientChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=300)


class PatientChatResponse(BaseModel):
    reply: str
    tool_calls: list[str] = Field(default_factory=list)


class AICommandCenterResponse(BaseModel):
    ai_calls: int
    failures: int
    fallback_rate: float
    total_cost_usd: Decimal
    thumbs_down_rate: float
    recent_runs: list[AIRunRead]
