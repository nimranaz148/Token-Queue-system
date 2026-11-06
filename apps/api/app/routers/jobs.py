import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_token
from app.schemas.auth import Role
from app.schemas.jobs import (
    DailyBriefJobRequest,
    DailyBriefJobResponse,
    DayCloseRequest,
    DayCloseResponse,
    EstimatesJobRequest,
    EstimatesJobResponse,
)
from app.services.jobs import JobsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def verify_jobs_caller(
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
    x_service_token: Annotated[str | None, Header(alias="X-Service-Token")] = None,
) -> None:
    """Verify that caller possesses the valid service token or administrative JWT."""
    token = x_service_token
    if not token and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]

    expected_secret = settings.jobs_service_token

    # 1. Direct match with configured service token
    if token and (token == expected_secret or token == settings.webhook_secret):
        return

    # 2. Check administrative JWT token
    if token:
        try:
            payload = decode_token(token)
            role = payload.get("role")
            is_admin = payload.get("is_platform_admin")
            if is_admin or role in {Role.PLATFORM_ADMIN, Role.OWNER}:
                return
        except Exception:
            pass

    # In development/test environments allow request if token is missing
    if settings.environment in ("development", "test") and not token:
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing service token.",
    )


@router.post("/day-close", response_model=DayCloseResponse, status_code=status.HTTP_200_OK)
async def trigger_day_close(
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: DayCloseRequest | None = None,
    _: None = Depends(verify_jobs_caller),
) -> DayCloseResponse:
    """Execute Day Close background job (W-006).

    - Marks unserved tokens (booked, arrived, skipped, hold) as no_show.
    - Marks serving tokens as done.
    - Writes immutable token_events and audit logs.
    - Upserts aggregated daily_stats per doctor.
    - Idempotent per clinic + date.
    """
    req = payload or DayCloseRequest()
    service = JobsService(session)
    return await service.run_day_close(
        clinic_id=req.clinic_id,
        target_date=req.date,
        force=req.force,
    )


@router.post("/daily-brief", response_model=DailyBriefJobResponse, status_code=status.HTTP_200_OK)
async def trigger_daily_brief(
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: DailyBriefJobRequest | None = None,
    _: None = Depends(verify_jobs_caller),
) -> DailyBriefJobResponse:
    """Execute Daily Brief background job (W-010).

    - Generates nightly AI brief summarizing patients, wait times, no-shows, and anomalies.
    - Writes ai_briefs and ai_runs.
    """
    req = payload or DailyBriefJobRequest()
    service = JobsService(session)
    return await service.run_daily_brief(
        clinic_id=req.clinic_id,
        target_date=req.date,
    )


@router.post("/estimates", response_model=EstimatesJobResponse, status_code=status.HTTP_200_OK)
async def trigger_estimates_refresh(
    session: Annotated[AsyncSession, Depends(get_db)],
    payload: EstimatesJobRequest | None = None,
    _: None = Depends(verify_jobs_caller),
) -> EstimatesJobResponse:
    """Execute Wait-Time Estimates refresh background job (PRD §3.3 & §13.2).

    - Predicts wait times for currently waiting tokens.
    - Persists estimates to wait_predictions table.
    """
    req = payload or EstimatesJobRequest()
    service = JobsService(session)
    return await service.run_estimates(
        clinic_id=req.clinic_id,
        doctor_id=req.doctor_id,
    )
