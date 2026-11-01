from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.ai.providers.gemini import GeminiProvider
from app.ai.types import AgentMessage, ToolDefinition


@pytest.fixture
def provider() -> GeminiProvider:
    return GeminiProvider(
        api_key="test-gemini-key",
        default_model="gemini-1.5-flash",
        timeout=5.0,
    )


@pytest.fixture
def sample_messages() -> list[AgentMessage]:
    return [
        AgentMessage(role="system", content="You are a clinic queue assistant."),
        AgentMessage(role="user", content="Mera token number 12 hai."),
    ]


@pytest.fixture
def sample_tools() -> list[ToolDefinition]:
    return [
        ToolDefinition(
            name="get_my_token_status",
            description="Check token number and people ahead",
            parameters={
                "type": "object",
                "properties": {
                    "public_code": {"type": "string"},
                },
                "required": ["public_code"],
            },
            required_roles=["public"],
        )
    ]


@pytest.mark.asyncio
async def test_gemini_happy_path_completion(
    provider: GeminiProvider, sample_messages: list[AgentMessage]
) -> None:
    """Acceptance test: Happy path chat completion against recorded Gemini response (I-005)."""
    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Aapka token check kar liya gaya hai."}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 95,
            "candidatesTokenCount": 30,
            "totalTokenCount": 125,
        },
    }

    mock_resp = httpx.Response(
        status_code=200,
        json=mock_response_data,
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await provider.complete(messages=sample_messages)

        assert result.provider == "gemini"
        assert result.content == "Aapka token check kar liya gaya hai."
        assert result.input_tokens == 95
        assert result.output_tokens == 30
        assert result.cost_usd > 0
        assert result.error is None


@pytest.mark.asyncio
async def test_gemini_tool_calling_response(
    provider: GeminiProvider,
    sample_messages: list[AgentMessage],
    sample_tools: list[ToolDefinition],
) -> None:
    """Acceptance test: Function call / tool call response parsed accurately from Gemini."""
    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "functionCall": {
                                "name": "get_my_token_status",
                                "args": {"public_code": "tok-789"},
                            }
                        }
                    ],
                    "role": "model",
                }
            }
        ],
        "usageMetadata": {"promptTokenCount": 75, "candidatesTokenCount": 20},
    }

    mock_resp = httpx.Response(
        status_code=200,
        json=mock_response_data,
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await provider.complete(messages=sample_messages, tools=sample_tools)

        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "get_my_token_status"
        assert result.tool_calls[0].arguments == {"public_code": "tok-789"}


@pytest.mark.asyncio
async def test_gemini_timeout_handling(
    provider: GeminiProvider, sample_messages: list[AgentMessage]
) -> None:
    """Acceptance test: Gemini timeout handled gracefully without crashing."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Gemini request timed out")

        result = await provider.complete(messages=sample_messages)

        assert result.content is None
        assert result.error is not None
        assert "timed out" in result.error.lower()


@pytest.mark.asyncio
async def test_gemini_error_response_handling(
    provider: GeminiProvider, sample_messages: list[AgentMessage]
) -> None:
    """Acceptance test: Gemini HTTP 503 unavailable or 400 error handled gracefully."""
    mock_resp = httpx.Response(
        status_code=503,
        text="Model overloaded",
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await provider.complete(messages=sample_messages)

        assert result.content is None
        assert result.error is not None
        assert "503" in result.error or "failed" in result.error.lower()


@pytest.mark.asyncio
async def test_gemini_duplicate_delivery_idempotency(
    provider: GeminiProvider, sample_messages: list[AgentMessage]
) -> None:
    """Acceptance test: Repeated identical calls return consistent response."""
    mock_response_data = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Consistent output"}],
                    "role": "model",
                }
            }
        ],
        "usageMetadata": {"promptTokenCount": 60, "candidatesTokenCount": 15},
    }

    mock_resp = httpx.Response(
        status_code=200,
        json=mock_response_data,
        request=httpx.Request("POST", "https://generativelanguage.googleapis.com"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        res1 = await provider.complete(messages=sample_messages)
        res2 = await provider.complete(messages=sample_messages)

        assert res1.content == res2.content == "Consistent output"
        assert res1.input_tokens == res2.input_tokens == 60
