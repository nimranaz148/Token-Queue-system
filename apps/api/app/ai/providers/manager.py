import logging

from app.ai.providers.base import AIProvider
from app.ai.providers.gemini import GeminiProvider
from app.ai.providers.openrouter import OpenRouterProvider
from app.ai.types import AgentMessage, AICompletionResult, ToolDefinition

logger = logging.getLogger(__name__)


class ProviderManager:
    """Manages AI completions across primary (OpenRouter) and fallback (Gemini) providers."""

    def __init__(
        self,
        primary: AIProvider | None = None,
        fallback: AIProvider | None = None,
    ) -> None:
        self.primary: AIProvider = primary or OpenRouterProvider()
        self.fallback: AIProvider = fallback or GeminiProvider()

    async def complete_with_fallback(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
    ) -> AICompletionResult:
        """
        Execute completion against primary provider with automatic fallback on failure/timeout.
        """
        # 1. Attempt primary provider (OpenRouter)
        try:
            result = await self.primary.complete(messages, tools, model=model)
            if not result.error:
                return result
            logger.warning(
                "Primary AI provider '%s' failed: %s. Initiating fallback...",
                self.primary.name,
                result.error,
            )
        except Exception as exc:
            logger.warning(
                "Primary AI provider '%s' exception: %s. Initiating fallback...",
                self.primary.name,
                str(exc),
            )

        # 2. Attempt fallback provider (Gemini)
        try:
            fallback_result = await self.fallback.complete(messages, tools)
            if not fallback_result.error:
                fallback_result.fallback_used = True
                return fallback_result
            logger.error(
                "Fallback AI provider '%s' also failed: %s.",
                self.fallback.name,
                fallback_result.error,
            )
            return AICompletionResult(
                provider=self.fallback.name,
                model="unknown",
                error=f"All AI providers failed. Fallback error: {fallback_result.error}",
                fallback_used=True,
            )
        except Exception as exc:
            logger.error(
                "Fallback AI provider '%s' exception: %s.",
                self.fallback.name,
                str(exc),
            )
            return AICompletionResult(
                provider=self.fallback.name,
                model="unknown",
                error=f"All AI providers failed: {str(exc)}",
                fallback_used=True,
            )
