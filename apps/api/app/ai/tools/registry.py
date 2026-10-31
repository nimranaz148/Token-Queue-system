import uuid
from typing import Any

from app.ai.tools.schemas import (
    DetectAnomaliesArgs,
    GetClinicInfoArgs,
    GetConsultDurationsArgs,
    GetDailyStatsArgs,
    GetMyTokenStatusArgs,
    GetPatientHistoryArgs,
    SaveWaitPredictionArgs,
)
from app.ai.types import CallerIdentity, ToolContext, ToolDefinition
from app.schemas.auth import Role

TOOL_DEFINITIONS: dict[str, ToolDefinition] = {
    "get_my_token_status": ToolDefinition(
        name="get_my_token_status",
        description="Fetch current token status, position in queue, and estimated wait time.",
        parameters=GetMyTokenStatusArgs.model_json_schema(),
        required_roles=["public"],
    ),
    "get_clinic_info": ToolDefinition(
        name="get_clinic_info",
        description="Fetch clinic basic details, timings, address, and active doctors.",
        parameters=GetClinicInfoArgs.model_json_schema(),
        required_roles=[
            "public",
            Role.PLATFORM_ADMIN,
            Role.OWNER,
            Role.DOCTOR,
            Role.RECEPTION,
            "system_job",
        ],
    ),
    "get_patient_history": ToolDefinition(
        name="get_patient_history",
        description="Fetch past consultation history for a patient in the clinic for doctor summary.",
        parameters=GetPatientHistoryArgs.model_json_schema(),
        required_roles=[Role.DOCTOR],
    ),
    "get_daily_stats": ToolDefinition(
        name="get_daily_stats",
        description="Fetch aggregated clinic statistics for evening business brief.",
        parameters=GetDailyStatsArgs.model_json_schema(),
        required_roles=[Role.OWNER, Role.PLATFORM_ADMIN, "system_job"],
    ),
    "detect_anomalies": ToolDefinition(
        name="detect_anomalies",
        description="Analyze daily clinic metrics to identify operational anomalies.",
        parameters=DetectAnomaliesArgs.model_json_schema(),
        required_roles=[Role.OWNER, Role.PLATFORM_ADMIN, "system_job"],
    ),
    "get_consult_durations": ToolDefinition(
        name="get_consult_durations",
        description="Retrieve recent consultation durations for a doctor to calculate wait estimates.",
        parameters=GetConsultDurationsArgs.model_json_schema(),
        required_roles=["system_job", Role.PLATFORM_ADMIN],
    ),
    "save_wait_prediction": ToolDefinition(
        name="save_wait_prediction",
        description="Record an AI-generated wait time prediction for a token.",
        parameters=SaveWaitPredictionArgs.model_json_schema(),
        required_roles=["system_job", Role.PLATFORM_ADMIN],
    ),
}


def check_tool_permission(
    tool_name: str, context: ToolContext, validated_args: dict[str, Any]
) -> tuple[bool, str | None]:
    """
    Validate that the caller has sufficient permissions and scope to invoke the tool.
    Enforces role authorization, public token binding, and tenant isolation.
    """
    tool_def = TOOL_DEFINITIONS.get(tool_name)
    if not tool_def:
        return False, f"Tool '{tool_name}' is not recognized in catalog"

    caller: CallerIdentity = context.caller

    # 1. Role permission check
    if caller.role not in tool_def.required_roles:
        return (
            False,
            f"Permission denied: role '{caller.role}' cannot invoke tool '{tool_name}'. "
            f"Allowed roles: {tool_def.required_roles}",
        )

    # 2. Public chat token binding (PRD §36.18: tool arguments come from session context)
    if tool_name == "get_my_token_status":
        requested_code = str(validated_args.get("public_code", ""))
        if not caller.public_code or caller.public_code != requested_code:
            return (
                False,
                "Permission denied: public chat can only query its own bound token public code",
            )

    # 3. Tenant scoping enforcement
    # If the tool takes clinic_id, caller must belong to that clinic (unless platform_admin, system_job, or public for clinic info)
    target_clinic_id = validated_args.get("clinic_id")
    if (
        target_clinic_id is not None
        and tool_name != "get_clinic_info"
        and caller.role not in (Role.PLATFORM_ADMIN, "system_job")
    ):
        if isinstance(target_clinic_id, str):
            target_clinic_id = uuid.UUID(target_clinic_id)
        if caller.clinic_id != target_clinic_id:
            return (
                False,
                f"Tenancy violation: caller from clinic {caller.clinic_id} cannot access data for clinic {target_clinic_id}",
            )

    return True, None
