import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.ai.providers.openrouter import OpenRouterProvider
from app.ai.types import AgentMessage, ToolDefinition


@pytest.fixture
def provider() -> OpenRouterProvider:
    return OpenRouterProvider(
        api_key="test-openrouter-key",
        base_url="https://openrouter.ai/api/v1",
        default_model="google/gemini-flash-1.5",
        timeout=5.0,
    )


@pytest.fixture
def sample_messages() -> list[AgentMessage]:
    return [
        AgentMessage(role="system", content="You are a clinic queue assistant."),
        AgentMessage(role="user", content="Mera token kab aayega?"),
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
async def test_openrouter_happy_path_completion(
    provider: OpenRouterProvider, sample_messages: list[AgentMessage]
) -> None:
    """Acceptance test: Happy path chat completion against recorded response (I-004)."""
    mock_response_data = {
        "id": "gen-12345",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Aapka token #12 hai. Aap se aagay 2 log hain.",
                }
            }
        ],
        "usage": {
            "prompt_tokens": 120,
            "completion_tokens": 25,
            "total_tokens": 145,
        },
    }

    mock_resp = httpx.Response(
        status_code=200,
        json=mock_response_data,
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await provider.complete(messages=sample_messages)

        assert result.provider == "openrouter"
        assert result.content == "Aapka token #12 hai. Aap se aagay 2 log hain."
        assert result.input_tokens == 120
        assert result.output_tokens == 25
        assert result.cost_usd > 0
        assert result.error is None


@pytest.mark.asyncio
async def test_openrouter_tool_calling_response(
    provider: OpenRouterProvider,
    sample_messages: list[AgentMessage],
    sample_tools: list[ToolDefinition],
) -> None:
    """Acceptance test: Function calling / tool call response parsed accurately."""
    mock_response_data = {
        "id": "gen-tool-123",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_abc",
                            "type": "function",
                            "function": {
                                "name": "get_my_token_status",
                                "arguments": json.dumps({"public_code": "tok-456"}),
                            },
                        }
                    ],
                }
            }
        ],
        "usage": {"prompt_tokens": 80, "completion_tokens": 15},
    }

    mock_resp = httpx.Response(
        status_code=200,
        json=mock_response_data,
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await provider.complete(messages=sample_messages, tools=sample_tools)

        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0].name == "get_my_token_status"
        assert result.tool_calls[0].arguments == {"public_code": "tok-456"}


@pytest.mark.asyncio
async def test_openrouter_timeout_handling(
    provider: OpenRouterProvider, sample_messages: list[AgentMessage]
) -> None:
    """Acceptance test: Provider timeout handled gracefully without crashing."""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("OpenRouter connection timed out")

        result = await provider.complete(messages=sample_messages)

        assert result.content is None
        assert result.error is not None
        assert "timed out" in result.error.lower()


@pytest.mark.asyncio
async def test_openrouter_error_response_handling(
    provider: OpenRouterProvider, sample_messages: list[AgentMessage]
) -> None:
    """Acceptance test: HTTP 429 rate limit or 500 error handled gracefully."""
    mock_resp = httpx.Response(
        status_code=429,
        text="Rate limit exceeded",
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        result = await provider.complete(messages=sample_messages)

        assert result.content is None
        assert result.error is not None
        assert "429" in result.error or "failed" in result.error.lower()


@pytest.mark.asyncio
async def test_openrouter_duplicate_delivery_idempotency(
    provider: OpenRouterProvider, sample_messages: list[AgentMessage]
) -> None:
    """Acceptance test: Repeated identical calls return consistent response."""
    mock_response_data = {
        "id": "gen-repeat-123",
        "choices": [{"message": {"role": "assistant", "content": "Same response"}}],
        "usage": {"prompt_tokens": 50, "completion_tokens": 10},
    }

    mock_resp = httpx.Response(
        status_code=200,
        json=mock_response_data,
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions"),
    )

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp

        res1 = await provider.complete(messages=sample_messages)
        res2 = await provider.complete(messages=sample_messages)

        assert res1.content == res2.content == "Same response"
        assert res1.input_tokens == res2.input_tokens == 50
