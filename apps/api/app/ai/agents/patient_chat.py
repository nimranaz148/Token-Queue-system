from typing import Any

from app.ai.guardrails import (
    MEDICAL_ADVICE_REFUSAL_MESSAGE,
    is_medical_advice_query,
    sanitize_patient_input,
)
from app.ai.protocols import AIDataServiceProtocol
from app.ai.providers.manager import ProviderManager
from app.ai.tools.executor import execute_tool
from app.ai.tools.registry import TOOL_DEFINITIONS
from app.ai.types import AgentMessage, AgentType, CallerIdentity, ToolContext


class PatientChatAgent:
    """
    Patient Queue Chat Agent (L1 autonomy).
    Answers questions about token status, queue position, and clinic info in Roman Urdu/English.
    """

    ALLOWED_TOOLS = ["get_my_token_status", "get_clinic_info"]

    def __init__(
        self,
        service: AIDataServiceProtocol,
        provider_manager: ProviderManager | None = None,
    ) -> None:
        self.service = service
        self.provider_manager = provider_manager or ProviderManager()

    async def answer(
        self,
        public_code: str,
        user_message: str,
        conversation_history: list[AgentMessage] | None = None,
    ) -> dict[str, Any]:
        """Process patient query with guardrails and tool execution."""
        # 1. Input sanitization (strip URLs, truncate to 300 chars)
        sanitized_input = sanitize_patient_input(user_message, max_length=300)

        # 2. Medical advice refusal guardrail
        if is_medical_advice_query(sanitized_input):
            return {
                "response": MEDICAL_ADVICE_REFUSAL_MESSAGE,
                "tool_calls": [],
                "fallback_used": False,
            }

        # 3. Spend cap check
        # For public tokens, check spend cap via service
        is_allowed = await self.service.check_spend_cap_allowed(clinic_id=None)
        if not is_allowed:
            return {
                "response": "Service is currently unavailable due to maintenance.",
                "tool_calls": [],
                "fallback_used": False,
            }

        # 4. Prepare caller context (bound to patient's public_code)
        caller = CallerIdentity(role="public", public_code=public_code)
        context = ToolContext(caller=caller)

        # 5. Build prompt and tool definitions
        tools = [TOOL_DEFINITIONS[name] for name in self.ALLOWED_TOOLS]
        system_prompt = (
            "You are a helpful clinic queue assistant for Pakistan clinics. "
            "Reply politely in Roman Urdu or English matching the patient's language. "
            "Only answer queue, token status, wait time, or clinic questions using the provided tools. "
            "Never give medical advice. Keep answers short and clear."
        )

        messages: list[AgentMessage] = [AgentMessage(role="system", content=system_prompt)]
        if conversation_history:
            messages.extend(conversation_history[-4:])  # recent context only
        messages.append(AgentMessage(role="user", content=sanitized_input))

        # 6. Execute completion
        completion = await self.provider_manager.complete_with_fallback(
            messages=messages,
            tools=tools,
        )

        executed_tools: list[dict[str, Any]] = []

        # 7. Execute tool calls if requested by model
        if completion.tool_calls:
            for tc in completion.tool_calls:
                if tc.name in self.ALLOWED_TOOLS:
                    # Enforce server-side public_code binding for get_my_token_status
                    tool_args = dict(tc.arguments)
                    if tc.name == "get_my_token_status":
                        tool_args["public_code"] = public_code

                    result = await execute_tool(
                        tool_name=tc.name,
                        raw_args=tool_args,
                        context=context,
                        service=self.service,
                    )
                    executed_tools.append(
                        {
                            "tool": tc.name,
                            "args": tool_args,
                            "success": result.success,
                            "data": result.data,
                            "error": result.error,
                        }
                    )

        # 8. Record telemetry in ai_runs
        await self.service.log_ai_run(
            {
                "feature": AgentType.PATIENT_CHAT.value,
                "provider": completion.provider,
                "model": completion.model,
                "tools_called": [t["tool"] for t in executed_tools],
                "input_tokens": completion.input_tokens,
                "output_tokens": completion.output_tokens,
                "cost_usd": completion.cost_usd,
                "status": "error" if completion.error else "success",
                "error": completion.error,
            }
        )

        final_text = (
            completion.content or "Aapka token status check kar liya gaya hai."
            if not completion.error
            else "Maazrat, system abhi masroof hai."
        )

        return {
            "response": final_text,
            "tool_calls": executed_tools,
            "fallback_used": completion.fallback_used,
        }
