import logging
import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import forbidden
from app.core.permissions import get_current_user
from app.schemas.auth import CurrentUser
from app.schemas.token import (
    DoctorHoldActionRequest,
    DoctorNextActionRequest,
    DoctorNextActionResponse,
    DoctorQueueResponse,
    DoctorRecallActionRequest,
    DoctorSkipActionRequest,
    ReceptionTokenListItem,
    ReceptionTokenListResponse,
    TokenCancelStaffRequest,
    WalkInTokenCreateRequest,
    WalkInTokenResponse,
)
from app.services.token import TokenService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tokens", tags=["tokens"])


@router.get("", response_model=ReceptionTokenListResponse, status_code=status.HTTP_200_OK)
async def list_tokens(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    target_date: Annotated[date | None, Query(alias="date")] = None,
    doctor_id: Annotated[uuid.UUID | None, Query()] = None,
    status_filter: Annotated[list[str] | None, Query(alias="status")] = None,
    search: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ReceptionTokenListResponse:
    """Retrieve tokens for Aaj ki List (PRD §5.3 F-004).

    Permissions: reception, owner, doctor (own queue).
    """
    effective_date = target_date or date.today()
    if not current_user.clinic_id:
        raise forbidden(
            code="CLINIC_REQUIRED", detail="User does not have an active clinic association."
        )
    service = TokenService(session)

    items, total = await service.list_reception_tokens(
        clinic_id=current_user.clinic_id,
        current_user=current_user,
        target_date=effective_date,
        doctor_id=doctor_id,
        status_filter=status_filter,
        search=search,
        limit=limit,
        offset=offset,
    )

    return ReceptionTokenListResponse(
        items=items,
        total=total,
        date=effective_date,
    )


@router.post("", response_model=WalkInTokenResponse, status_code=status.HTTP_201_CREATED)
async def create_walk_in_token(
    payload: WalkInTokenCreateRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> WalkInTokenResponse:
    """Issue a walk-in token at reception (PRD §5.3 F-005, W-002).

    Permissions: reception, owner.
    """
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    if not current_user.clinic_id:
        raise forbidden(
            code="CLINIC_REQUIRED", detail="User does not have an active clinic association."
        )
    service = TokenService(session)

    return await service.create_walk_in_token(
        clinic_id=current_user.clinic_id,
        payload=payload,
        current_user=current_user,
        client_ip=client_ip,
        request_id=request_id,
    )


@router.post(
    "/{token_id}/arrive", response_model=ReceptionTokenListItem, status_code=status.HTTP_200_OK
)
async def mark_token_arrived(
    token_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReceptionTokenListItem:
    """Mark a booked token arrived (PRD §5.3 F-004, W-003).

    Permissions: reception, owner.
    """
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    if not current_user.clinic_id:
        raise forbidden(
            code="CLINIC_REQUIRED", detail="User does not have an active clinic association."
        )
    service = TokenService(session)

    return await service.mark_token_arrived(
        clinic_id=current_user.clinic_id,
        token_id=token_id,
        current_user=current_user,
        client_ip=client_ip,
        request_id=request_id,
    )


@router.post(
    "/{token_id}/cancel", response_model=ReceptionTokenListItem, status_code=status.HTTP_200_OK
)
async def cancel_token(
    token_id: uuid.UUID,
    body: TokenCancelStaffRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ReceptionTokenListItem:
    """Cancel a token with mandatory reason (PRD §5.3 F-004, W-005).

    Permissions: reception, owner.
    """
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    if not current_user.clinic_id:
        raise forbidden(
            code="CLINIC_REQUIRED", detail="User does not have an active clinic association."
        )
    service = TokenService(session)

    return await service.cancel_token_by_staff(
        clinic_id=current_user.clinic_id,
        token_id=token_id,
        reason=body.reason,
        current_user=current_user,
        client_ip=client_ip,
        request_id=request_id,
    )


# -----------------------------------------------------------------------------
# Doctor Panel Queue Operations (PRD §5.3 F-007, W-004)
# -----------------------------------------------------------------------------


@router.get("/doctor/queue", response_model=DoctorQueueResponse, status_code=status.HTTP_200_OK)
async def get_doctor_queue(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    doctor_id: Annotated[uuid.UUID | None, Query()] = None,
    target_date: Annotated[date | None, Query(alias="date")] = None,
) -> DoctorQueueResponse:
    """Retrieve doctor consultation panel queue (PRD §5.3 F-007).

    Permissions: doctor, owner.
    """
    if not current_user.clinic_id:
        raise forbidden(
            code="CLINIC_REQUIRED", detail="User does not have an active clinic association."
        )
    service = TokenService(session)
    return await service.get_doctor_queue(
        clinic_id=current_user.clinic_id,
        doctor_id=doctor_id,
        visit_date=target_date,
        current_user=current_user,
    )


@router.post(
    "/doctor/next", response_model=DoctorNextActionResponse, status_code=status.HTTP_200_OK
)
async def doctor_call_next(
    payload: DoctorNextActionRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorNextActionResponse:
    """Advance to next patient: complete current serving and call next (F-007, W-004).

    Permissions: doctor, owner.
    """
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    if not current_user.clinic_id:
        raise forbidden(
            code="CLINIC_REQUIRED", detail="User does not have an active clinic association."
        )
    service = TokenService(session)
    return await service.call_next_patient(
        clinic_id=current_user.clinic_id,
        doctor_id=payload.doctor_id,
        quick_note=payload.quick_note,
        current_user=current_user,
        client_ip=client_ip,
        request_id=request_id,
    )


@router.post(
    "/doctor/skip", response_model=DoctorNextActionResponse, status_code=status.HTTP_200_OK
)
async def doctor_skip_patient(
    payload: DoctorSkipActionRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorNextActionResponse:
    """Skip currently serving patient (F-007, W-004).

    Permissions: doctor, owner.
    """
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    if not current_user.clinic_id:
        raise forbidden(
            code="CLINIC_REQUIRED", detail="User does not have an active clinic association."
        )
    service = TokenService(session)
    return await service.skip_current_patient(
        clinic_id=current_user.clinic_id,
        doctor_id=payload.doctor_id,
        current_user=current_user,
        client_ip=client_ip,
        request_id=request_id,
    )


@router.post(
    "/doctor/hold", response_model=DoctorNextActionResponse, status_code=status.HTTP_200_OK
)
async def doctor_hold_patient(
    payload: DoctorHoldActionRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorNextActionResponse:
    """Place currently serving patient on hold with optional reason (F-007, W-004).

    Permissions: doctor, owner.
    """
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    if not current_user.clinic_id:
        raise forbidden(
            code="CLINIC_REQUIRED", detail="User does not have an active clinic association."
        )
    service = TokenService(session)
    return await service.hold_current_patient(
        clinic_id=current_user.clinic_id,
        doctor_id=payload.doctor_id,
        reason=payload.reason,
        current_user=current_user,
        client_ip=client_ip,
        request_id=request_id,
    )


@router.post(
    "/doctor/recall", response_model=DoctorNextActionResponse, status_code=status.HTTP_200_OK
)
async def doctor_recall_patient(
    payload: DoctorRecallActionRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorNextActionResponse:
    """Recall a skipped or hold patient back to the front of queue (F-007, W-004).

    Permissions: doctor, owner.
    """
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    if not current_user.clinic_id:
        raise forbidden(
            code="CLINIC_REQUIRED", detail="User does not have an active clinic association."
        )
    service = TokenService(session)
    return await service.recall_patient(
        clinic_id=current_user.clinic_id,
        doctor_id=payload.doctor_id,
        token_id=payload.token_id,
        current_user=current_user,
        client_ip=client_ip,
        request_id=request_id,
    )
