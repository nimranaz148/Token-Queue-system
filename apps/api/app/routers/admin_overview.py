import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_platform_admin
from app.schemas.admin_overview import PlatformOverviewResponse
from app.schemas.auth import CurrentUser
from app.services.admin_overview import AdminOverviewService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/overview", tags=["admin-overview"])


@router.get("", response_model=PlatformOverviewResponse, status_code=status.HTTP_200_OK)
async def get_platform_overview(
    _admin: Annotated[CurrentUser, Depends(require_platform_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PlatformOverviewResponse:
    """Retrieve platform-wide operational KPIs and clinic activity table (PRD §29.2 D-002).

    Permissions: platform_admin only.
    """
    service = AdminOverviewService(session)
    return await service.get_overview()
