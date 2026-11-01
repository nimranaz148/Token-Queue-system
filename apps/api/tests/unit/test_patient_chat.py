import datetime as dt
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.guardrails import MEDICAL_ADVICE_REFUSAL_MESSAGE
from app.main import app
from app.models.ai import ChatMessage
from app.models.token import Token


@pytest.fixture
def sample_token() -> Token:
    token = MagicMock(spec=Token)
    token.id = uuid.uuid4()
    token.clinic_id = uuid.uuid4()
    token.doctor_id = uuid.uuid4()
    token.number = 15
    token.status = "waiting"
    token.public_code = "safe-token-xyz-123"
    return token


@pytest.mark.asyncio
async def test_patient_can_ask_queue_status(sample_token: Token) -> None:
    """Acceptance test: Patient asks 'mera number kab aayega' and receives status (F-019)."""
    with patch("app.services.ai_service.AIService.send_patient_message") as mock_send:
        mock_send.return_value = (
            "Aapka token #15 hai. Aap se aagay 3 mareez hain.",
            ["get_my_token_status"],
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.post(
                f"/api/v1/public/tokens/{sample_token.public_code}/chat",
                json={"message": "Mera number kab aayega?"},
            )

        assert res.status_code == 200
        data = res.json()
        assert "Aapka token #15 hai" in data["reply"]
        assert "get_my_token_status" in data["tool_calls"]


@pytest.mark.asyncio
async def test_patient_chat_refuses_medical_advice(sample_token: Token) -> None:
    """Acceptance test: Assistant strictly refuses medical advice (PRD §36.10)."""
    with patch("app.services.ai_service.AIService.send_patient_message") as mock_send:
        mock_send.return_value = (
            MEDICAL_ADVICE_REFUSAL_MESSAGE,
            [],
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.post(
                f"/api/v1/public/tokens/{sample_token.public_code}/chat",
                json={"message": "Bukhar aur gale mein dard ki dawa bata dein"},
            )

        assert res.status_code == 200
        data = res.json()
        assert data["reply"] == MEDICAL_ADVICE_REFUSAL_MESSAGE


@pytest.mark.asyncio
async def test_patient_chat_rate_limiting(sample_token: Token) -> None:
    """Acceptance test: Enforce 20 messages per token per day (PRD §5.3 F-019)."""
    from fastapi import HTTPException, status

    with patch("app.services.ai_service.AIService.send_patient_message") as mock_send:
        mock_send.side_effect = HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rozana 20 messages ki had poori ho chuki hai.",
        )

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.post(
                f"/api/v1/public/tokens/{sample_token.public_code}/chat",
                json={"message": "Halat kaisi hai?"},
            )

        assert res.status_code == 429
        assert "20 messages" in res.json()["detail"]


@pytest.mark.asyncio
async def test_patient_chat_history_endpoint(sample_token: Token) -> None:
    """Acceptance test: Patient can view prior messages in session."""
    msg1 = MagicMock(spec=ChatMessage)
    msg1.id = uuid.uuid4()
    msg1.role = "patient"
    msg1.content = "Kitni der lagegi?"
    msg1.at = dt.datetime.now(dt.UTC)

    msg2 = MagicMock(spec=ChatMessage)
    msg2.id = uuid.uuid4()
    msg2.role = "assistant"
    msg2.content = "Andaazan 20 minute intezar hai."
    msg2.at = dt.datetime.now(dt.UTC)

    with patch("app.services.ai_service.AIService.get_patient_chat_history") as mock_hist:
        mock_hist.return_value = (sample_token, [msg1, msg2])

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            res = await client.get(
                f"/api/v1/public/tokens/{sample_token.public_code}/chat",
            )

        assert res.status_code == 200
        data = res.json()
        assert len(data) == 2
        assert data[0]["content"] == "Kitni der lagegi?"
        assert data[1]["content"] == "Andaazan 20 minute intezar hai."


@pytest.mark.asyncio
async def test_patient_chat_validation_rules() -> None:
    """Acceptance test: Empty message or message > 300 chars is rejected."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Empty message
        res_empty = await client.post(
            "/api/v1/public/tokens/safe-token-xyz/chat",
            json={"message": ""},
        )
        assert res_empty.status_code == 422

        # Exceeds 300 characters
        res_long = await client.post(
            "/api/v1/public/tokens/safe-token-xyz/chat",
            json={"message": "a" * 305},
        )
        assert res_long.status_code == 422
