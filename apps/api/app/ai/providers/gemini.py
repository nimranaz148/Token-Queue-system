from typing import Any

import httpx

from app.ai.providers.base import AIProvider
from app.ai.types import AgentMessage, AICompletionResult, ToolCall, ToolDefinition
from app.core.config import settings


class GeminiProvider(AIProvider):
    """Fallback AI provider using Google Gemini API."""

    def __init__(
        self,
        api_key: str | None = None,
        default_model: str | None = None,
        timeout: float = 20.0,
    ) -> None:
        self.api_key = api_key or settings.gemini_api_key
        self.default_model = default_model or settings.gemini_default_model
        self.timeout = timeout

    @property
    def name(self) -> str:
        return "gemini"

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
                error="Gemini API key is not configured",
            )

        target_model = model or self.default_model

        # Convert messages to Gemini contents structure
        contents: list[dict[str, Any]] = []
        for msg in messages:
            role = "model" if msg.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": msg.content}]})

        payload: dict[str, Any] = {"contents": contents}

        if tools:
            # Map tools to Gemini function declarations
            function_declarations = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
                for tool in tools
            ]
            payload["tools"] = [{"functionDeclarations": function_declarations}]

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{target_model}:generateContent?key={self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            candidates = data.get("candidates", [])
            if not candidates:
                return AICompletionResult(
                    provider=self.name,
                    model=target_model,
                    error="Gemini returned no candidates",
                )

            parts = candidates[0].get("content", {}).get("parts", [])
            text_content = ""
            tool_calls: list[ToolCall] = []

            for part in parts:
                if "text" in part:
                    text_content += part["text"]
                elif "functionCall" in part:
                    fn = part["functionCall"]
                    tool_calls.append(
                        ToolCall(
                            id=fn.get("name", ""),
                            name=fn.get("name", ""),
                            arguments=fn.get("args", {}),
                        )
                    )

            usage = data.get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)

            # Gemini Flash pricing approx: $0.075 / 1M prompt, $0.30 / 1M completion
            cost_usd = (input_tokens * 0.000000075) + (output_tokens * 0.00000030)

            return AICompletionResult(
                content=text_content if text_content else None,
                tool_calls=tool_calls if tool_calls else None,
                provider=self.name,
                model=target_model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                fallback_used=True,
            )

        except Exception as exc:
            return AICompletionResult(
                provider=self.name,
                model=target_model,
                error=f"Gemini request failed: {str(exc)}",
            )
