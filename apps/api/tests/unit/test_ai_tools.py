import uuid
from datetime import date
from typing import Any

import pytest

from app.ai.agents.daily_brief import DailyBriefAgent
from app.ai.agents.patient_chat import PatientChatAgent
from app.ai.agents.visit_summarizer import VisitSummarizerAgent
from app.ai.agents.wait_predictor import WaitPredictorAgent
from app.ai.guardrails import (
    MEDICAL_ADVICE_REFUSAL_MESSAGE,
    is_medical_advice_query,
    mask_pii_for_ai,
    sanitize_patient_input,
)
from app.ai.providers.base import AIProvider
from app.ai.providers.manager import ProviderManager
from app.ai.tools.executor import execute_tool
from app.ai.types import (
    AgentMessage,
    AICompletionResult,
    CallerIdentity,
    ToolContext,
    ToolDefinition,
)
from app.schemas.auth import Role


class MockAIDataService:
    """Mock domain service implementing AIDataServiceProtocol for unit testing."""

    def __init__(self) -> None:
        self.ai_notes_enabled = True
        self.spend_cap_allowed = True
        self.logged_runs: list[dict[str, Any]] = []
        self.saved_predictions: list[dict[str, Any]] = []

    async def get_token_status_by_code(self, public_code: str) -> dict[str, Any]:
        return {
            "token_number": 42,
            "status": "waiting",
            "people_ahead": 3,
            "estimated_wait_minutes": 30,
        }

    async def get_clinic_info(self, clinic_id: uuid.UUID) -> dict[str, Any]:
        return {
            "name": "Al-Shifa Clinic",
            "address": "Main Boulevard, Lahore",
            "phone": "03001234567",
        }

    async def get_patient_history(
        self, patient_id: uuid.UUID, clinic_id: uuid.UUID
    ) -> dict[str, Any]:
        return {
            "patient_id": str(patient_id),
            "visits": [
                {
                    "complaint": "Viral fever",
                    "medicines_advice": "Panadol 500mg tds",
                    "created_at": "2026-10-15T10:00:00Z",
                }
            ],
        }

    async def is_ai_notes_enabled(self, clinic_id: uuid.UUID) -> bool:
        return self.ai_notes_enabled

    async def get_daily_stats(
        self, clinic_id: uuid.UUID, start_date: date, end_date: date
    ) -> dict[str, Any]:
        return {
            "total_tokens": 50,
            "completed_tokens": 45,
            "cancelled_tokens": 2,
            "no_show_tokens": 3,
        }

    async def detect_anomalies(
        self, clinic_id: uuid.UUID, target_date: date
    ) -> list[dict[str, Any]]:
        return [{"type": "HIGH_NO_SHOW_RATE", "description": "No-shows spike"}]

    async def get_consult_durations(self, doctor_id: uuid.UUID, limit: int) -> list[int]:
        return [10, 15, 8]

    async def save_wait_prediction(
        self,
        token_id: uuid.UUID,
        clinic_id: uuid.UUID,
        predicted_minutes: int,
        model_version: str,
    ) -> dict[str, Any]:
        record = {
            "token_id": str(token_id),
            "clinic_id": str(clinic_id),
            "predicted_minutes": predicted_minutes,
            "model_version": model_version,
        }
        self.saved_predictions.append(record)
        return record

    async def check_spend_cap_allowed(self, clinic_id: uuid.UUID | None) -> bool:
        return self.spend_cap_allowed

    async def log_ai_run(self, run_data: dict[str, Any]) -> None:
        self.logged_runs.append(run_data)


# ---------------------------------------------------------------------------
# Tool Catalog & Permission Unit Tests (PRD §36.4, PRD §36.20)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_tool_get_my_token_status_authorization() -> None:
    service = MockAIDataService()
    valid_code = "safe-token-abc"

    # Happy path: public caller with matching public code
    ctx_valid = ToolContext(caller=CallerIdentity(role="public", public_code=valid_code))
    res_valid = await execute_tool(
        "get_my_token_status", {"public_code": valid_code}, ctx_valid, service
    )
    assert res_valid.success is True
    assert res_valid.data["token_number"] == 42

    # Sad path: public caller with mismatched code (cannot peek at others)
    ctx_invalid = ToolContext(caller=CallerIdentity(role="public", public_code="other-code"))
    res_invalid = await execute_tool(
        "get_my_token_status", {"public_code": valid_code}, ctx_invalid, service
    )
    assert res_invalid.success is False
    assert "FORBIDDEN" in (res_invalid.error or "")

    # Sad path: role not allowed
    ctx_reception = ToolContext(caller=CallerIdentity(role=Role.RECEPTION, public_code=valid_code))
    res_role = await execute_tool(
        "get_my_token_status", {"public_code": valid_code}, ctx_reception, service
    )
    assert res_role.success is False
    assert "FORBIDDEN" in (res_role.error or "")


@pytest.mark.asyncio
async def test_tool_get_clinic_info_public_access() -> None:
    service = MockAIDataService()
    clinic_id = uuid.uuid4()
    ctx = ToolContext(caller=CallerIdentity(role="public"))

    res = await execute_tool("get_clinic_info", {"clinic_id": str(clinic_id)}, ctx, service)
    assert res.success is True
    assert res.data["name"] == "Al-Shifa Clinic"
    # PII masking should mask phone number
    assert res.data["phone"] == "[PHONE_MASKED]"


@pytest.mark.asyncio
async def test_tool_get_patient_history_doctor_and_tenancy() -> None:
    service = MockAIDataService()
    clinic_a = uuid.uuid4()
    clinic_b = uuid.uuid4()
    patient_id = uuid.uuid4()

    # Doctor of clinic A accessing clinic A -> success
    ctx_doc_a = ToolContext(caller=CallerIdentity(role=Role.DOCTOR, clinic_id=clinic_a))
    res = await execute_tool(
        "get_patient_history",
        {"patient_id": str(patient_id), "clinic_id": str(clinic_a)},
        ctx_doc_a,
        service,
    )
    assert res.success is True

    # Doctor of clinic A accessing clinic B -> Tenancy violation
    res_cross = await execute_tool(
        "get_patient_history",
        {"patient_id": str(patient_id), "clinic_id": str(clinic_b)},
        ctx_doc_a,
        service,
    )
    assert res_cross.success is False
    assert "Tenancy violation" in (res_cross.error or "")

    # Reception attempting history -> Forbidden
    ctx_rec = ToolContext(caller=CallerIdentity(role=Role.RECEPTION, clinic_id=clinic_a))
    res_rec = await execute_tool(
        "get_patient_history",
        {"patient_id": str(patient_id), "clinic_id": str(clinic_a)},
        ctx_rec,
        service,
    )
    assert res_rec.success is False
    assert "FORBIDDEN" in (res_rec.error or "")


@pytest.mark.asyncio
async def test_tool_get_patient_history_requires_ai_notes_enabled() -> None:
    service = MockAIDataService()
    service.ai_notes_enabled = False  # Clinic has turned it OFF
    clinic_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    ctx = ToolContext(caller=CallerIdentity(role=Role.DOCTOR, clinic_id=clinic_id))
    res = await execute_tool(
        "get_patient_history",
        {"patient_id": str(patient_id), "clinic_id": str(clinic_id)},
        ctx,
        service,
    )
    assert res.success is False
    assert "ai_notes_enabled turned OFF" in (res.error or "")


@pytest.mark.asyncio
async def test_tool_daily_stats_and_anomalies_owner_only() -> None:
    service = MockAIDataService()
    clinic_id = uuid.uuid4()

    # Owner -> Success
    ctx_owner = ToolContext(caller=CallerIdentity(role=Role.OWNER, clinic_id=clinic_id))
    res_stats = await execute_tool(
        "get_daily_stats",
        {"clinic_id": str(clinic_id), "start_date": "2026-10-01", "end_date": "2026-10-07"},
        ctx_owner,
        service,
    )
    assert res_stats.success is True
    assert res_stats.data["total_tokens"] == 50

    # Doctor -> Forbidden
    ctx_doc = ToolContext(caller=CallerIdentity(role=Role.DOCTOR, clinic_id=clinic_id))
    res_doc = await execute_tool(
        "get_daily_stats",
        {"clinic_id": str(clinic_id), "start_date": "2026-10-01", "end_date": "2026-10-07"},
        ctx_doc,
        service,
    )
    assert res_doc.success is False
    assert "FORBIDDEN" in (res_doc.error or "")


@pytest.mark.asyncio
async def test_tool_system_job_predictions() -> None:
    service = MockAIDataService()
    token_id = uuid.uuid4()
    clinic_id = uuid.uuid4()

    ctx_system = ToolContext(caller=CallerIdentity(role="system_job", clinic_id=clinic_id))
    res = await execute_tool(
        "save_wait_prediction",
        {
            "token_id": str(token_id),
            "clinic_id": str(clinic_id),
            "predicted_minutes": 25,
            "model_version": "v1",
        },
        ctx_system,
        service,
    )
    assert res.success is True
    assert len(service.saved_predictions) == 1

    # Public attempting prediction save -> Forbidden
    ctx_pub = ToolContext(caller=CallerIdentity(role="public"))
    res_pub = await execute_tool(
        "save_wait_prediction",
        {
            "token_id": str(token_id),
            "clinic_id": str(clinic_id),
            "predicted_minutes": 25,
        },
        ctx_pub,
        service,
    )
    assert res_pub.success is False
    assert "FORBIDDEN" in (res_pub.error or "")


# ---------------------------------------------------------------------------
# Guardrails Unit Tests (PRD §36.10, §36.18)
# ---------------------------------------------------------------------------


def test_sanitize_patient_input() -> None:
    raw = "Meri bari kab aye gi? check https://badsite.com and www.phish.org/link shukriya"
    cleaned = sanitize_patient_input(raw, max_length=300)
    assert "https://" not in cleaned
    assert "www." not in cleaned
    assert "Meri bari kab aye gi?" in cleaned
    assert "shukriya" in cleaned

    # Length truncation
    long_text = "a" * 400
    assert len(sanitize_patient_input(long_text, max_length=300)) == 300


def test_medical_advice_detection() -> None:
    assert is_medical_advice_query("Doctor sahab mujhe tez bukhar hai konsi dawa loon?") is True
    assert is_medical_advice_query("What tablet should I take for pain?") is True
    assert is_medical_advice_query("Mera token number 12 hai, kitna time lagay ga?") is False


def test_pii_masking() -> None:
    data = {
        "patient_name": "Ali Hassan",
        "phone": "03001234567",
        "nested": {"contact": "03219876543"},
    }
    masked = mask_pii_for_ai(data)
    assert masked["patient_name"] == "Ali"
    assert masked["phone"] == "[PHONE_MASKED]"
    assert masked["nested"]["contact"] == "[PHONE_MASKED]"


# ---------------------------------------------------------------------------
# Provider Fallback Unit Tests (PRD §36.22, I-004 -> I-005)
# ---------------------------------------------------------------------------


class MockFailingProvider(AIProvider):
    @property
    def name(self) -> str:
        return "mock_primary_fail"

    async def complete(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
    ) -> AICompletionResult:
        return AICompletionResult(
            provider=self.name,
            model="fail-model",
            error="Connection timed out after 20s",
        )


class MockHealthyProvider(AIProvider):
    @property
    def name(self) -> str:
        return "mock_gemini_fallback"

    async def complete(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
    ) -> AICompletionResult:
        return AICompletionResult(
            content="Fallback answer: aapka token 5 minutes me call hoga.",
            provider=self.name,
            model="gemini-1.5-flash",
            fallback_used=True,
        )


class MockCustomProvider(AIProvider):
    def __init__(self, result: AICompletionResult) -> None:
        self._result = result

    @property
    def name(self) -> str:
        return "mock_custom"

    async def complete(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
    ) -> AICompletionResult:
        return self._result


@pytest.mark.asyncio
async def test_provider_manager_fallback_behavior() -> None:
    primary = MockFailingProvider()
    fallback = MockHealthyProvider()
    manager = ProviderManager(primary=primary, fallback=fallback)

    result = await manager.complete_with_fallback(
        messages=[AgentMessage(role="user", content="kya status hai?")]
    )
    assert result.error is None
    assert result.fallback_used is True
    assert result.provider == "mock_gemini_fallback"
    assert "aapka token" in (result.content or "")


# ---------------------------------------------------------------------------
# Agent Orchestration Tests (PRD §36.10, §36.11, §36.12, §36.13)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patient_chat_agent_medical_refusal() -> None:
    service = MockAIDataService()
    agent = PatientChatAgent(service=service)

    reply = await agent.answer(
        public_code="safe-code-1",
        user_message="Doctor sahab mujhe bukhar hai dawa bata dain",
    )
    assert reply["response"] == MEDICAL_ADVICE_REFUSAL_MESSAGE
    assert len(reply["tool_calls"]) == 0


@pytest.mark.asyncio
async def test_patient_chat_agent_spend_cap_enforcement() -> None:
    service = MockAIDataService()
    service.spend_cap_allowed = False  # Cap exceeded
    agent = PatientChatAgent(service=service)

    reply = await agent.answer(
        public_code="safe-code-1",
        user_message="Mera number kab aye ga?",
    )
    assert "unavailable" in reply["response"].lower()


@pytest.mark.asyncio
async def test_visit_summarizer_agent() -> None:
    service = MockAIDataService()
    mock_provider = MockCustomProvider(
        result=AICompletionResult(
            content="• 2026-10-15: Viral fever diagnosed, Panadol prescribed.",
            provider="openrouter",
            model="gpt-4o-mini",
        )
    )
    manager = ProviderManager(primary=mock_provider, fallback=mock_provider)
    agent = VisitSummarizerAgent(service=service, provider_manager=manager)

    doc_id = uuid.uuid4()
    clinic_id = uuid.uuid4()
    patient_id = uuid.uuid4()

    summary_res = await agent.summarize_history(doc_id, clinic_id, patient_id)
    assert "AI summary - check before use" in summary_res["summary"]
    assert "Viral fever" in summary_res["summary"]
    assert len(service.logged_runs) == 1


@pytest.mark.asyncio
async def test_daily_brief_agent() -> None:
    service = MockAIDataService()
    mock_provider = MockCustomProvider(
        result=AICompletionResult(
            content="Clinic served 45 patients with 3 no-shows. Operations remained stable.",
            provider="openrouter",
            model="gpt-4o-mini",
        )
    )
    manager = ProviderManager(primary=mock_provider, fallback=mock_provider)
    agent = DailyBriefAgent(service=service, provider_manager=manager)

    clinic_id = uuid.uuid4()
    brief = await agent.generate_brief(clinic_id, date(2026, 10, 31))
    assert "served 45 patients" in brief["brief_md"]
    assert len(brief["anomalies"]) > 0


@pytest.mark.asyncio
async def test_wait_predictor_agent() -> None:
    service = MockAIDataService()
    agent = WaitPredictorAgent(service=service)

    token_id = uuid.uuid4()
    clinic_id = uuid.uuid4()
    doctor_id = uuid.uuid4()

    pred = await agent.predict_and_save(token_id, clinic_id, doctor_id, people_ahead=3)
    assert pred["saved"] is True
    assert pred["predicted_minutes"] > 0
    assert len(service.saved_predictions) == 1
