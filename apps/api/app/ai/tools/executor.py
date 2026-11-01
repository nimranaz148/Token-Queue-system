from typing import Any

from pydantic import BaseModel, ValidationError

from app.ai.guardrails import mask_pii_for_ai
from app.ai.protocols import AIDataServiceProtocol
from app.ai.tools.registry import check_tool_permission
from app.ai.tools.schemas import (
    DetectAnomaliesArgs,
    GetClinicInfoArgs,
    GetConsultDurationsArgs,
    GetDailyStatsArgs,
    GetMyTokenStatusArgs,
    GetPatientHistoryArgs,
    SaveWaitPredictionArgs,
)
from app.ai.types import ToolContext, ToolResult

ARG_SCHEMAS: dict[str, type[BaseModel]] = {
    "get_my_token_status": GetMyTokenStatusArgs,
    "get_clinic_info": GetClinicInfoArgs,
    "get_patient_history": GetPatientHistoryArgs,
    "get_daily_stats": GetDailyStatsArgs,
    "detect_anomalies": DetectAnomaliesArgs,
    "get_consult_durations": GetConsultDurationsArgs,
    "save_wait_prediction": SaveWaitPredictionArgs,
}


async def execute_tool(
    tool_name: str,
    raw_args: dict[str, Any],
    context: ToolContext,
    service: AIDataServiceProtocol,
) -> ToolResult:
    """Execute a registered tool within the caller's authorized context."""
    schema_cls = ARG_SCHEMAS.get(tool_name)
    if not schema_cls:
        return ToolResult(success=False, error=f"Tool '{tool_name}' has no defined argument schema")

    # 1. Validate argument types and structure
    try:
        validated_args = schema_cls.model_validate(raw_args)
    except ValidationError as e:
        return ToolResult(
            success=False,
            error=f"Argument validation failed for tool '{tool_name}': {e.errors()}",
        )

    args_dict = validated_args.model_dump()

    # 2. Enforce permission, identity binding, and tenant scoping
    is_allowed, reason = check_tool_permission(tool_name, context, args_dict)
    if not is_allowed:
        return ToolResult(success=False, error=f"FORBIDDEN: {reason}")

    # 3. Special compliance check for patient visit notes
    if tool_name == "get_patient_history" and isinstance(validated_args, GetPatientHistoryArgs):
        clinic_id = validated_args.clinic_id
        notes_enabled = await service.is_ai_notes_enabled(clinic_id)
        if not notes_enabled:
            return ToolResult(
                success=False,
                error="AI summary disabled: clinic settings have ai_notes_enabled turned OFF",
            )

    # 4. Dispatch to domain service
    data: Any = None
    try:
        if tool_name == "get_my_token_status":
            data = await service.get_token_status_by_code(args_dict["public_code"])
        elif tool_name == "get_clinic_info":
            data = await service.get_clinic_info(args_dict["clinic_id"])
        elif tool_name == "get_patient_history":
            data = await service.get_patient_history(
                args_dict["patient_id"], args_dict["clinic_id"]
            )
        elif tool_name == "get_daily_stats":
            data = await service.get_daily_stats(
                args_dict["clinic_id"], args_dict["start_date"], args_dict["end_date"]
            )
        elif tool_name == "detect_anomalies":
            data = await service.detect_anomalies(args_dict["clinic_id"], args_dict["target_date"])
        elif tool_name == "get_consult_durations":
            data = await service.get_consult_durations(args_dict["doctor_id"], args_dict["limit"])
        elif tool_name == "save_wait_prediction":
            data = await service.save_wait_prediction(
                args_dict["token_id"],
                args_dict["clinic_id"],
                args_dict["predicted_minutes"],
                args_dict["model_version"],
            )
        else:
            return ToolResult(success=False, error=f"Unhandled tool '{tool_name}' execution")

        # Minimize PII before returning data to AI agents
        if isinstance(data, dict):
            data = mask_pii_for_ai(data)
        elif isinstance(data, list):
            data = [mask_pii_for_ai(item) if isinstance(item, dict) else item for item in data]

        return ToolResult(success=True, data=data)
    except Exception as exc:
        return ToolResult(
            success=False,
            error=f"Error executing tool '{tool_name}': {str(exc)}",
        )
