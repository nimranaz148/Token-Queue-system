import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import forbidden
from app.core.permissions import require_roles
from app.schemas.auth import CurrentUser, Role
from app.schemas.settings import ClinicSettingsRead, ClinicSettingsUpdate
from app.services.settings import SettingsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])


def resolve_clinic_id(
    current_user: CurrentUser,
    active_clinic_id: str | None = None,
    x_clinic_id: str | None = None,
) -> uuid.UUID:
    """Resolve effective clinic UUID from session, cookie, or header."""
    if current_user.clinic_id:
        return current_user.clinic_id
    if active_clinic_id:
        try:
            return uuid.UUID(active_clinic_id)
        except ValueError:
            pass
    if x_clinic_id:
        try:
            return uuid.UUID(x_clinic_id)
        except ValueError:
            pass
    raise forbidden(
        code="CLINIC_REQUIRED",
        detail="User does not have an active clinic association.",
    )


@router.get("", response_model=ClinicSettingsRead, status_code=status.HTTP_200_OK)
async def get_clinic_settings(
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.OWNER, Role.PLATFORM_ADMIN)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
    active_clinic_id: Annotated[str | None, Cookie()] = None,
    x_clinic_id: Annotated[str | None, Header(alias="X-Clinic-ID")] = None,
) -> ClinicSettingsRead:
    """Retrieve clinic operational settings and tenant profile (PRD §5.3 F-011).

    Permissions: owner, platform_admin.
    """
    clinic_id = resolve_clinic_id(current_user, active_clinic_id, x_clinic_id)
    service = SettingsService(session)
    return await service.get_settings(clinic_id=clinic_id, current_user=current_user)


@router.put("", response_model=ClinicSettingsRead, status_code=status.HTTP_200_OK)
async def update_clinic_settings(
    payload: ClinicSettingsUpdate,
    request: Request,
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.OWNER, Role.PLATFORM_ADMIN)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
    active_clinic_id: Annotated[str | None, Cookie()] = None,
    x_clinic_id: Annotated[str | None, Header(alias="X-Clinic-ID")] = None,
) -> ClinicSettingsRead:
    """Update clinic operational settings with optimistic locking and audit trail (PRD §5.3 F-011).

    Permissions: owner, platform_admin.
    """
    clinic_id = resolve_clinic_id(current_user, active_clinic_id, x_clinic_id)
    service = SettingsService(session)
    client_ip = request.client.host if request.client else None
    request_id = request.headers.get("x-request-id")

    return await service.update_settings(
        clinic_id=clinic_id,
        payload=payload,
        current_user=current_user,
        client_ip=client_ip,
        request_id=request_id,
    )
