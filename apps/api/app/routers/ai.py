import datetime as dt
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import forbidden
from app.core.permissions import require_roles
from app.schemas.ai import (
    AIActivityResponse,
    AIBriefFeedbackRequest,
    AIBriefRead,
    AICommandCenterResponse,
    AIRunRead,
)
from app.schemas.auth import CurrentUser, Role
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get(
    "/activity",
    response_model=AIActivityResponse,
    status_code=status.HTTP_200_OK,
)
async def get_ai_activity(
    current_user: Annotated[CurrentUser, Depends(require_roles(Role.OWNER, Role.PLATFORM_ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    start_date: Annotated[dt.date | None, Query(description="Start date filter")] = None,
    end_date: Annotated[dt.date | None, Query(description="End date filter")] = None,
    feature: Annotated[str | None, Query(description="Feature filter")] = None,
    clinic_id: Annotated[
        uuid.UUID | None, Query(description="Platform admin clinic filter")
    ] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AIActivityResponse:
    """Retrieve AI execution telemetry log (F-017).

    Owners view their clinic's runs; Platform Admins can view all runs or filter by clinic.
    """
    is_admin = current_user.role == Role.PLATFORM_ADMIN
    service = AIService(session)
    items, total = await service.get_activity_log(
        caller_clinic_id=current_user.clinic_id,
        is_platform_admin=is_admin,
        start_date=start_date,
        end_date=end_date,
        feature=feature,
        filter_clinic_id=clinic_id,
        limit=limit,
        offset=offset,
    )
    return AIActivityResponse(
        items=[AIRunRead.model_validate(i) for i in items],
        total=total,
    )


@router.get(
    "/command-center",
    response_model=AICommandCenterResponse,
    status_code=status.HTTP_200_OK,
)
async def get_ai_command_center(
    current_user: Annotated[CurrentUser, Depends(require_roles(Role.OWNER, Role.PLATFORM_ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    clinic_id: Annotated[
        uuid.UUID | None, Query(description="Filter by clinic (admin only)")
    ] = None,
) -> AICommandCenterResponse:
    """Retrieve AI Command Center KPIs and recent runs (D-003)."""
    is_admin = current_user.role == Role.PLATFORM_ADMIN
    service = AIService(session)
    kpis = await service.get_command_center_kpis(
        caller_clinic_id=current_user.clinic_id,
        is_platform_admin=is_admin,
        filter_clinic_id=clinic_id if is_admin else None,
    )
    return AICommandCenterResponse(
        ai_calls=kpis["ai_calls"],
        failures=kpis["failures"],
        fallback_rate=kpis["fallback_rate"],
        total_cost_usd=kpis["total_cost_usd"],
        thumbs_down_rate=kpis["thumbs_down_rate"],
        recent_runs=[AIRunRead.model_validate(r) for r in kpis["recent_runs"]],
    )


@router.get(
    "/daily-brief",
    response_model=AIBriefRead,
    status_code=status.HTTP_200_OK,
)
async def get_daily_brief(
    current_user: Annotated[CurrentUser, Depends(require_roles(Role.OWNER, Role.PLATFORM_ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    brief_date: Annotated[dt.date | None, Query(alias="date")] = None,
) -> AIBriefRead:
    """Retrieve the daily brief for the owner's clinic on a specific date (F-018)."""
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Clinic context required.")
    target_date = brief_date or dt.date.today()
    service = AIService(session)
    brief = await service.get_daily_brief(clinic_id=current_user.clinic_id, target_date=target_date)
    return AIBriefRead.model_validate(brief)


@router.post(
    "/daily-brief/generate",
    response_model=AIBriefRead,
    status_code=status.HTTP_200_OK,
)
async def generate_daily_brief(
    current_user: Annotated[CurrentUser, Depends(require_roles(Role.OWNER, Role.PLATFORM_ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
    brief_date: Annotated[dt.date | None, Query(alias="date")] = None,
) -> AIBriefRead:
    """Generate or re-generate the daily brief for the owner's clinic (F-018)."""
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Clinic context required.")
    target_date = brief_date or dt.date.today()
    service = AIService(session)
    brief = await service.generate_daily_brief(
        clinic_id=current_user.clinic_id,
        target_date=target_date,
        requested_by=current_user.user_id,
    )
    return AIBriefRead.model_validate(brief)


@router.post(
    "/daily-brief/{brief_id}/feedback",
    response_model=AIBriefRead,
    status_code=status.HTTP_200_OK,
)
async def submit_brief_feedback(
    brief_id: uuid.UUID,
    payload: AIBriefFeedbackRequest,
    current_user: Annotated[CurrentUser, Depends(require_roles(Role.OWNER, Role.PLATFORM_ADMIN))],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AIBriefRead:
    """Record owner thumbs up/down feedback for evaluation tracking (F-018)."""
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Clinic context required.")
    service = AIService(session)
    brief = await service.submit_brief_feedback(
        clinic_id=current_user.clinic_id,
        brief_id=brief_id,
        feedback=payload.feedback,
    )
    return AIBriefRead.model_validate(brief)
