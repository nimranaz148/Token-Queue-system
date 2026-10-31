from abc import ABC, abstractmethod

from app.ai.types import AgentMessage, AICompletionResult, ToolDefinition


class AIProvider(ABC):
    """Abstract interface for AI model completion providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name identifier."""
        ...

    @abstractmethod
    async def complete(
        self,
        messages: list[AgentMessage],
        tools: list[ToolDefinition] | None = None,
        model: str | None = None,
    ) -> AICompletionResult:
        """Generate a chat completion response with optional tool calling."""
        ...
