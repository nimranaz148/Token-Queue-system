import uuid
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(StrEnum):
    PATIENT_CHAT = "patient_chat"
    VISIT_SUMMARIZER = "visit_summarizer"
    DAILY_BRIEF = "daily_brief"
    WAIT_PREDICTOR = "wait_predictor"


class CallerIdentity(BaseModel):
    """Identity context of the entity making the AI request or invoking a tool."""

    role: str
    clinic_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    doctor_id: uuid.UUID | None = None
    public_code: str | None = None


class ToolContext(BaseModel):
    """Context passed into tool execution."""

    caller: CallerIdentity
    request_id: str | None = None


class ToolCall(BaseModel):
    """Represents a tool call invocation requested by the model."""

    id: str
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class AgentMessage(BaseModel):
    """Message exchanged in an agent conversation."""

    role: str  # system, user, assistant, tool
    content: str
    name: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None


class ToolDefinition(BaseModel):
    """Metadata schema defining an agent tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    required_roles: list[str]


class ToolResult(BaseModel):
    """Standard result returned by any tool execution."""

    success: bool
    data: Any = None
    error: str | None = None


class AICompletionResult(BaseModel):
    """Result returned by an AI provider completion."""

    content: str | None = None
    tool_calls: list[ToolCall] | None = None
    provider: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    fallback_used: bool = False
    error: str | None = None
