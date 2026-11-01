import datetime as dt
import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import forbidden
from app.core.permissions import require_roles
from app.schemas.auth import CurrentUser, Role
from app.schemas.report import DailyReportResponse
from app.services.report import ReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/daily", response_model=DailyReportResponse, status_code=status.HTTP_200_OK)
async def get_daily_report(
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.OWNER, Role.DOCTOR, Role.PLATFORM_ADMIN)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
    target_date: Annotated[dt.date | None, Query(alias="date")] = None,
    doctor_id: Annotated[uuid.UUID | None, Query()] = None,
    clinic_id: Annotated[uuid.UUID | None, Query()] = None,
    active_clinic_id: Annotated[str | None, Cookie()] = None,
    x_clinic_id: Annotated[str | None, Header(alias="X-Clinic-ID")] = None,
) -> DailyReportResponse:
    """Retrieve Roz ki Report daily KPI metrics and 7-day trend (PRD §5.3 F-010 / §29.1 D-001).

    Permissions: owner, doctor (own queue only).
    """
    effective_clinic_id = current_user.clinic_id or clinic_id
    if not effective_clinic_id and active_clinic_id:
        try:
            effective_clinic_id = uuid.UUID(active_clinic_id)
        except ValueError:
            pass
    if not effective_clinic_id and x_clinic_id:
        try:
            effective_clinic_id = uuid.UUID(x_clinic_id)
        except ValueError:
            pass

    if not effective_clinic_id:
        raise forbidden(
            code="CLINIC_REQUIRED", detail="User does not have an active clinic association."
        )

    effective_date = target_date or dt.date.today()
    service = ReportService(session)

    return await service.get_daily_report(
        clinic_id=effective_clinic_id,
        target_date=effective_date,
        current_user=current_user,
        doctor_id=doctor_id,
    )
