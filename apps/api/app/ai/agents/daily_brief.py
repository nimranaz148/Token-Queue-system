import uuid
from datetime import date, timedelta
from typing import Any

from app.ai.protocols import AIDataServiceProtocol
from app.ai.providers.manager import ProviderManager
from app.ai.tools.executor import execute_tool
from app.ai.types import AgentMessage, AgentType, CallerIdentity, ToolContext
from app.schemas.auth import Role


class DailyBriefAgent:
    """
    Daily Evening Brief Agent (L1-L2 autonomy).
    Generates a concise nightly summary (<= 150 words) covering patients, wait times,
    no-shows, 7-day average comparison, and up to 3 operational anomalies.
    """

    def __init__(
        self,
        service: AIDataServiceProtocol,
        provider_manager: ProviderManager | None = None,
    ) -> None:
        self.service = service
        self.provider_manager = provider_manager or ProviderManager()

    async def generate_brief(
        self,
        clinic_id: uuid.UUID,
        target_date: date,
        requested_by: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Generate daily business brief for clinic owner."""
        # 1. Caller identity (owner or system job)
        caller = CallerIdentity(
            role=Role.OWNER if requested_by else "system_job",
            clinic_id=clinic_id,
            user_id=requested_by,
        )
        context = ToolContext(caller=caller)

        # 2. Fetch stats for the last 7 days for comparison
        start_date = target_date - timedelta(days=7)
        stats_result = await execute_tool(
            tool_name="get_daily_stats",
            raw_args={
                "clinic_id": clinic_id,
                "start_date": start_date,
                "end_date": target_date,
            },
            context=context,
            service=self.service,
        )

        # 3. Detect anomalies
        anomaly_result = await execute_tool(
            tool_name="detect_anomalies",
            raw_args={"clinic_id": clinic_id, "target_date": target_date},
            context=context,
            service=self.service,
        )

        anomalies = anomaly_result.data if anomaly_result.success else []
        stats = stats_result.data if stats_result.success else {}

        # 4. Synthesize brief prompt (strictly enforcing <= 150 words)
        prompt = (
            f"Generate a nightly clinic business brief in under 150 words for {target_date}.\n"
            f"Key metrics: {stats}\n"
            f"Detected anomalies (mention at most 3): {anomalies}\n"
            "Include: total patients served, average wait time, no-show rate vs 7-day average, "
            "and concise actionable highlights."
        )

        completion = await self.provider_manager.complete_with_fallback(
            messages=[
                AgentMessage(
                    role="system",
                    content="You are an executive healthcare operations analyst. Write crisp, high-value briefs.",
                ),
                AgentMessage(role="user", content=prompt),
            ]
        )

        # 5. Log telemetry
        await self.service.log_ai_run(
            {
                "clinic_id": clinic_id,
                "feature": AgentType.DAILY_BRIEF.value,
                "requested_by": requested_by,
                "provider": completion.provider,
                "model": completion.model,
                "tools_called": ["get_daily_stats", "detect_anomalies"],
                "input_tokens": completion.input_tokens,
                "output_tokens": completion.output_tokens,
                "cost_usd": completion.cost_usd,
                "status": "error" if completion.error else "success",
                "error": completion.error,
            }
        )

        brief_text = completion.content or "Daily brief generation unavailable."

        return {
            "date": target_date,
            "brief_md": brief_text,
            "anomalies": anomalies[:3] if isinstance(anomalies, list) else [],
            "fallback_used": completion.fallback_used,
        }
