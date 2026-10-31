import uuid
from typing import Any

from app.ai.protocols import AIDataServiceProtocol
from app.ai.providers.manager import ProviderManager
from app.ai.tools.executor import execute_tool
from app.ai.types import AgentMessage, AgentType, CallerIdentity, ToolContext
from app.schemas.auth import Role

SUMMARY_DISCLAIMER_HEADER = "⚠️ AI summary - check before use\n"


class VisitSummarizerAgent:
    """
    Doctor Visit Summarizer Agent (L1 autonomy).
    Summarizes at most the last 10 patient visits into <= 5 bullet points with dates.
    """

    def __init__(
        self,
        service: AIDataServiceProtocol,
        provider_manager: ProviderManager | None = None,
    ) -> None:
        self.service = service
        self.provider_manager = provider_manager or ProviderManager()

    async def summarize_history(
        self,
        doctor_id: uuid.UUID,
        clinic_id: uuid.UUID,
        patient_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Summarize patient history for doctor."""
        # 1. Compliance check: clinic must have ai_notes_enabled switched ON
        if not await self.service.is_ai_notes_enabled(clinic_id):
            return {
                "error": "AI notes summarization is disabled for this clinic.",
                "summary": None,
            }

        # 2. Spend cap check
        if not await self.service.check_spend_cap_allowed(clinic_id):
            return {
                "error": "Monthly AI spend cap reached for this clinic.",
                "summary": None,
            }

        # 3. Caller identity & context (enforces doctor role & clinic scope)
        caller = CallerIdentity(
            role=Role.DOCTOR,
            clinic_id=clinic_id,
            user_id=doctor_id,
            doctor_id=doctor_id,
        )
        context = ToolContext(caller=caller)

        # 4. Fetch history via tool layer
        result = await execute_tool(
            tool_name="get_patient_history",
            raw_args={"patient_id": patient_id, "clinic_id": clinic_id},
            context=context,
            service=self.service,
        )

        if not result.success:
            return {
                "error": f"Failed to retrieve patient history: {result.error}",
                "summary": None,
            }

        history_data = result.data or {}
        visits = history_data.get("visits", [])[:10]  # At most last 10 visits

        if not visits:
            return {
                "summary": f"{SUMMARY_DISCLAIMER_HEADER}No previous visits recorded for this patient.",
                "visits_count": 0,
            }

        # 5. Format prompt for LLM
        prompt = (
            "Summarise the following patient visits into at most 5 concise bullet points. "
            "Include the visit date for each bullet. Never invent symptoms or diagnoses absent from the records.\n\n"
            f"Visits:\n{visits}"
        )

        completion = await self.provider_manager.complete_with_fallback(
            messages=[
                AgentMessage(
                    role="system",
                    content="You are a clinical history summarizer. Adhere strictly to provided records.",
                ),
                AgentMessage(role="user", content=prompt),
            ]
        )

        # 6. Log telemetry
        await self.service.log_ai_run(
            {
                "clinic_id": clinic_id,
                "feature": AgentType.VISIT_SUMMARIZER.value,
                "requested_by": doctor_id,
                "provider": completion.provider,
                "model": completion.model,
                "tools_called": ["get_patient_history"],
                "input_tokens": completion.input_tokens,
                "output_tokens": completion.output_tokens,
                "cost_usd": completion.cost_usd,
                "status": "error" if completion.error else "success",
                "error": completion.error,
            }
        )

        summary_body = completion.content or "Summary generation unavailable."
        return {
            "summary": f"{SUMMARY_DISCLAIMER_HEADER}{summary_body}",
            "visits_count": len(visits),
            "fallback_used": completion.fallback_used,
        }
