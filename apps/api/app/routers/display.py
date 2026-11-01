import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import forbidden, unauthorized
from app.core.permissions import require_roles
from app.schemas.auth import CurrentUser, Role
from app.schemas.display import (
    DisplayDeviceResponse,
    DisplayFeedResponse,
    DisplayPairCompleteRequest,
    DisplayPairCompleteResponse,
    DisplayPairInitiateRequest,
    DisplayPairInitiateResponse,
)
from app.services.display import DisplayService

router = APIRouter(prefix="/display", tags=["Display Device & TV Screen (F-009, F-020)"])


@router.post(
    "/pairing/initiate",
    response_model=DisplayPairInitiateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_display_pairing(
    payload: DisplayPairInitiateRequest,
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.OWNER)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DisplayPairInitiateResponse:
    """Generate 6-character pairing code for waiting room TV (PRD §5.3 F-020)."""
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Clinic context required.")
    service = DisplayService(session)
    return await service.initiate_pairing(
        clinic_id=current_user.clinic_id,
        payload=payload,
        current_user=current_user,
    )


@router.post(
    "/pairing/complete",
    response_model=DisplayPairCompleteResponse,
    status_code=status.HTTP_200_OK,
)
async def complete_display_pairing(
    payload: DisplayPairCompleteRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DisplayPairCompleteResponse:
    """Validate pairing code entered on /tv and receive long-lived device token (PRD §5.3 F-020)."""
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    service = DisplayService(session)
    return await service.complete_pairing(
        payload=payload,
        client_ip=client_ip,
        request_id=request_id,
    )


@router.get(
    "/devices",
    response_model=list[DisplayDeviceResponse],
    status_code=status.HTTP_200_OK,
)
async def list_display_devices(
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.OWNER)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[DisplayDeviceResponse]:
    """List paired TV display devices for the clinic (PRD §5.3 F-020)."""
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Clinic context required.")
    service = DisplayService(session)
    return await service.list_devices(
        clinic_id=current_user.clinic_id,
        current_user=current_user,
    )


@router.post(
    "/devices/{device_id}/revoke",
    response_model=DisplayDeviceResponse,
    status_code=status.HTTP_200_OK,
)
async def revoke_display_device(
    device_id: uuid.UUID,
    request: Request,
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.OWNER)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DisplayDeviceResponse:
    """Revoke authorization for a waiting room TV display device (PRD §5.3 F-020)."""
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Clinic context required.")
    service = DisplayService(session)
    return await service.revoke_device(
        clinic_id=current_user.clinic_id,
        device_id=device_id,
        current_user=current_user,
        client_ip=client_ip,
        request_id=request_id,
    )


@router.get(
    "/feed",
    response_model=DisplayFeedResponse,
    status_code=status.HTTP_200_OK,
)
async def get_display_feed(
    authorization: Annotated[str | None, Header()] = None,
    session: Annotated[AsyncSession, Depends(get_db)] = None,
) -> DisplayFeedResponse:
    """Retrieve live queue feed for paired TV screen. Token numbers only (PRD §5.3 F-009, Rule 10)."""
    if not authorization or not authorization.startswith("Bearer "):
        raise unauthorized(code="UNAUTHORIZED", detail="Device Bearer token required.")

    device_token = authorization.removeprefix("Bearer ").strip()
    service = DisplayService(session)
    return await service.get_display_feed(device_token=device_token)
