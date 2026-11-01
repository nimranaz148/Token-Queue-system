import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import forbidden
from app.core.permissions import require_clinic_member, require_roles
from app.schemas.auth import CurrentUser, Role
from app.schemas.doctor import (
    DoctorCreate,
    DoctorListResponse,
    DoctorResponse,
    DoctorScheduleCreate,
    DoctorScheduleResponse,
    DoctorUpdate,
)
from app.services.doctor import DoctorService

router = APIRouter(prefix="/doctors", tags=["Doctor Management"])

owner_required = require_roles(Role.OWNER)


@router.get(
    "",
    response_model=DoctorListResponse,
    summary="List doctors for the clinic tenant (F-016)",
)
async def list_doctors(
    current_user: Annotated[CurrentUser, Depends(require_clinic_member)],
    session: Annotated[AsyncSession, Depends(get_db)],
    active_only: Annotated[bool, Query(description="Filter active doctors only")] = False,
) -> DoctorListResponse:
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Active clinic session required")

    service = DoctorService(session)
    items, total = await service.list_doctors(
        clinic_id=current_user.clinic_id,
        active_only=active_only,
    )
    return DoctorListResponse(items=items, total=total)


@router.get(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Get doctor details including weekly OPD schedule (F-016)",
)
async def get_doctor(
    doctor_id: uuid.UUID,
    current_user: Annotated[CurrentUser, Depends(require_clinic_member)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorResponse:
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Active clinic session required")

    service = DoctorService(session)
    return await service.get_doctor(
        clinic_id=current_user.clinic_id,
        doctor_id=doctor_id,
    )


@router.post(
    "",
    response_model=DoctorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new doctor for the clinic (F-016)",
)
async def create_doctor(
    data: DoctorCreate,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(owner_required)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorResponse:
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Active clinic session required")

    ip_address = request.client.host if request.client else None
    request_id = request.headers.get("x-request-id")

    service = DoctorService(session)
    return await service.create_doctor(
        clinic_id=current_user.clinic_id,
        data=data,
        actor_id=current_user.user_id,
        client_ip=ip_address,
        request_id=request_id,
    )


@router.patch(
    "/{doctor_id}",
    response_model=DoctorResponse,
    summary="Update doctor profile, limits, and status (F-016)",
)
async def update_doctor(
    doctor_id: uuid.UUID,
    data: DoctorUpdate,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(owner_required)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorResponse:
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Active clinic session required")

    ip_address = request.client.host if request.client else None
    request_id = request.headers.get("x-request-id")

    service = DoctorService(session)
    return await service.update_doctor(
        clinic_id=current_user.clinic_id,
        doctor_id=doctor_id,
        data=data,
        actor_id=current_user.user_id,
        client_ip=ip_address,
        request_id=request_id,
    )


@router.put(
    "/{doctor_id}/schedule",
    response_model=list[DoctorScheduleResponse],
    summary="Replace weekly OPD schedule for a doctor (F-016)",
)
async def update_schedules(
    doctor_id: uuid.UUID,
    schedules: list[DoctorScheduleCreate],
    request: Request,
    current_user: Annotated[CurrentUser, Depends(owner_required)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[DoctorScheduleResponse]:
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Active clinic session required")

    ip_address = request.client.host if request.client else None
    request_id = request.headers.get("x-request-id")

    service = DoctorService(session)
    return await service.update_schedules(
        clinic_id=current_user.clinic_id,
        doctor_id=doctor_id,
        schedules=schedules,
        actor_id=current_user.user_id,
        client_ip=ip_address,
        request_id=request_id,
    )


@router.delete(
    "/{doctor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete doctor and deactivate OPD queue (F-016)",
)
async def delete_doctor(
    doctor_id: uuid.UUID,
    request: Request,
    current_user: Annotated[CurrentUser, Depends(owner_required)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Active clinic session required")

    ip_address = request.client.host if request.client else None
    request_id = request.headers.get("x-request-id")

    service = DoctorService(session)
    await service.delete_doctor(
        clinic_id=current_user.clinic_id,
        doctor_id=doctor_id,
        actor_id=current_user.user_id,
        client_ip=ip_address,
        request_id=request_id,
    )
