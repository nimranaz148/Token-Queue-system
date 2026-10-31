import json
from typing import Any

import httpx

from app.ai.providers.base import AIProvider
from app.ai.types import AgentMessage, AICompletionResult, ToolCall, ToolDefinition
from app.core.config import settings


class OpenRouterProvider(AIProvider):
    """Primary AI provider using OpenRouter OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        default_model: str | None = None,
        timeout: float = 20.0,
    ) -> None:
        self.api_key = api_key or settings.openrouter_api_key
        self.base_url = (base_url or settings.openrouter_base_url).rstrip("/")
        self.default_model = default_model or settings.openrouter_default_model
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "openrouter"

    async def complete(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
    ) -> AICompletionResult:
        if not self.api_key:
            return AICompletionResult(
                provider=self.name,
                model=model or self.default_model,
                error="OpenRouter API key is not configured",
            )

        target_model = model or self.default_model
        formatted_messages: list[dict[str, Any]] = [
            {"role": msg.role, "content": msg.content} for msg in messages
        ]

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": formatted_messages,
        }

        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in tools
            ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://clinic-saas.local",
            "X-Title": "Clinic Token & Queue SaaS",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            choice = data["choices"][0]["message"]
            usage = data.get("usage", {})
            input_tokens = usage.get("prompt_tokens", 0)
            output_tokens = usage.get("completion_tokens", 0)

            # Estimate cost: $0.15 / 1M prompt, $0.60 / 1M completion for mini models
            cost_usd = (input_tokens * 0.00000015) + (output_tokens * 0.00000060)

            tool_calls: list[ToolCall] | None = None
            if "tool_calls" in choice and choice["tool_calls"]:
                tool_calls = []
                for tc in choice["tool_calls"]:
                    fn = tc.get("function", {})
                    args = fn.get("arguments", "{}")
                    parsed_args = json.loads(args) if isinstance(args, str) else args
                    tool_calls.append(
                        ToolCall(
                            id=tc.get("id", ""),
                            name=fn.get("name", ""),
                            arguments=parsed_args,
                        )
                    )

            return AICompletionResult(
                content=choice.get("content"),
                tool_calls=tool_calls,
                provider=self.name,
                model=target_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                fallback_used=False,
            )

        except Exception as exc:
            return AICompletionResult(
                provider=self.name,
                model=target_model,
                error=f"OpenRouter request failed: {str(exc)}",
            )
