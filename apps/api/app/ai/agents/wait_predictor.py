import uuid
from typing import Any

from app.ai.protocols import AIDataServiceProtocol
from app.ai.tools.executor import execute_tool
from app.ai.types import CallerIdentity, ToolContext


class WaitPredictorAgent:
    """
    Wait Time Predictor Agent (L4 autonomy, restricted to estimate writes only).
    Calculates estimated wait minutes based on trailing consult durations and queue state,
    then saves the estimate to wait_predictions table.
    """

    def __init__(self, service: AIDataServiceProtocol) -> None:
        self.service = service

    async def predict_and_save(
        self,
        token_id: uuid.UUID,
        clinic_id: uuid.UUID,
        doctor_id: uuid.UUID,
        people_ahead: int,
    ) -> dict[str, Any]:
        """Predict wait time and record prediction estimate."""
        caller = CallerIdentity(role="system_job", clinic_id=clinic_id)
        context = ToolContext(caller=caller)

        # 1. Fetch recent consult durations for the doctor
        durations_result = await execute_tool(
            tool_name="get_consult_durations",
            raw_args={"doctor_id": doctor_id, "limit": 10},
            context=context,
            service=self.service,
        )

        durations: list[int] = durations_result.data if durations_result.success else []
        if durations:
            avg_duration = sum(durations) / len(durations)
        else:
            avg_duration = 10.0  # Default 10 min consult fallback

        # Formula calculation: people ahead * avg consult duration
        predicted_minutes = max(0, int(round(people_ahead * avg_duration)))

        # 2. Save prediction estimate via tool layer
        save_result = await execute_tool(
            tool_name="save_wait_prediction",
            raw_args={
                "token_id": token_id,
                "clinic_id": clinic_id,
                "predicted_minutes": predicted_minutes,
                "model_version": "heuristic_v1",
            },
            context=context,
            service=self.service,
        )

        return {
            "token_id": token_id,
            "predicted_minutes": predicted_minutes,
            "saved": save_result.success,
            "error": save_result.error,
        }
