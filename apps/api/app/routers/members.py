import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import forbidden
from app.core.permissions import require_roles
from app.schemas.auth import CurrentUser, Role
from app.schemas.member import (
    MemberInviteRequest,
    MemberListResponse,
    MemberResponse,
    MemberUpdateRequest,
)
from app.services.member import MemberService

router = APIRouter(prefix="/members", tags=["Staff Management"])

owner_required = require_roles(Role.OWNER)


@router.get(
    "",
    response_model=MemberListResponse,
    summary="List staff members for the authenticated owner's clinic",
)
async def list_members(
    current_user: Annotated[CurrentUser, Depends(owner_required)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> MemberListResponse:
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Active clinic session required")

    service = MemberService(session)
    items, total = await service.list_members(current_user.clinic_id)
    return MemberListResponse(
        items=[MemberResponse(**item) for item in items],
        total=total,
    )


@router.post(
    "",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite/create a new staff member (F-015)",
)
async def invite_member(
    data: MemberInviteRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(owner_required)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_agent: Annotated[str | None, Header()] = None,
) -> MemberResponse:
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Active clinic session required")

    ip_address = request.client.host if request.client else None
    service = MemberService(session)
    member = await service.invite_member(
        clinic_id=current_user.clinic_id,
        current_user=current_user,
        data=data,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return MemberResponse(**member)


@router.patch(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Update staff member role, doctor link, or active status",
)
async def update_member(
    member_id: uuid.UUID,
    data: MemberUpdateRequest,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(owner_required)],
    session: Annotated[AsyncSession, Depends(get_db)],
    user_agent: Annotated[str | None, Header()] = None,
) -> MemberResponse:
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Active clinic session required")

    ip_address = request.client.host if request.client else None
    service = MemberService(session)
    member = await service.update_member(
        clinic_id=current_user.clinic_id,
        member_id=member_id,
        current_user=current_user,
        data=data,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return MemberResponse(**member)
