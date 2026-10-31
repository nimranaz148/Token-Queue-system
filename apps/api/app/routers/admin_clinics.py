import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_platform_admin
from app.schemas.auth import CurrentUser
from app.schemas.clinic import (
    ClinicCreate,
    ClinicListResponse,
    ClinicResponse,
    ClinicStatusUpdate,
)
from app.services.clinic import ClinicService

router = APIRouter(prefix="/admin/clinics", tags=["admin-clinics"])


@router.post("", response_model=ClinicResponse, status_code=status.HTTP_201_CREATED)
async def create_clinic(
    req: ClinicCreate,
    request: Request,
    admin: Annotated[CurrentUser, Depends(require_platform_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicResponse:
    """Create a new clinic tenant in 'trial' status (PRD F-013). Requires platform_admin."""
    service = ClinicService(session)
    client_ip = request.client.host if request.client else None
    clinic = await service.create_clinic(
        data=req,
        created_by=admin.user_id,
        ip_address=client_ip,
    )
    return ClinicResponse.model_validate(clinic)


@router.get("", response_model=ClinicListResponse)
async def list_clinics(
    _admin: Annotated[CurrentUser, Depends(require_platform_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
    search: str | None = Query(default=None, description="Search clinics by name or slug"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> ClinicListResponse:
    """List all registered clinic tenants with optional search (PRD F-014). Requires platform_admin."""
    service = ClinicService(session)
    items, total = await service.list_clinics(search=search, limit=limit, offset=offset)
    return ClinicListResponse(
        items=[ClinicResponse.model_validate(c) for c in items],
        total=total,
    )


@router.get("/{clinic_id}", response_model=ClinicResponse)
async def get_clinic(
    clinic_id: uuid.UUID,
    _admin: Annotated[CurrentUser, Depends(require_platform_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicResponse:
    """Get details for a specific clinic. Requires platform_admin."""
    service = ClinicService(session)
    clinic = await service.get_clinic(clinic_id)
    return ClinicResponse.model_validate(clinic)


@router.patch("/{clinic_id}/status", response_model=ClinicResponse)
async def update_clinic_status(
    clinic_id: uuid.UUID,
    req: ClinicStatusUpdate,
    request: Request,
    admin: Annotated[CurrentUser, Depends(require_platform_admin)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> ClinicResponse:
    """Suspend or activate a clinic (PRD F-014 row action). Requires platform_admin."""
    service = ClinicService(session)
    client_ip = request.client.host if request.client else None
    clinic = await service.update_status(
        clinic_id=clinic_id,
        new_status=req.status,
        reason=req.reason,
        changed_by=admin.user_id,
        ip_address=client_ip,
    )
    return ClinicResponse.model_validate(clinic)
