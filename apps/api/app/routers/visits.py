import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import forbidden
from app.core.permissions import require_roles
from app.schemas.auth import CurrentUser, Role
from app.schemas.visit import (
    PatientHistoryResponse,
    VisitCreateRequest,
    VisitListItem,
    VisitUpdateRequest,
)
from app.services.visit import VisitService

router = APIRouter(prefix="/visits", tags=["Visits & Clinical Notes (F-008)"])


@router.get(
    "/patient/{patient_id}",
    response_model=PatientHistoryResponse,
    status_code=status.HTTP_200_OK,
)
async def get_patient_history(
    patient_id: uuid.UUID,
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.DOCTOR, Role.OWNER)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PatientHistoryResponse:
    """Retrieve full visit timeline and clinical history for a patient (PRD §5.3 F-008)."""
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Clinic context required.")
    service = VisitService(session)
    return await service.get_patient_history(
        clinic_id=current_user.clinic_id,
        patient_id=patient_id,
        current_user=current_user,
    )


@router.post(
    "",
    response_model=VisitListItem,
    status_code=status.HTTP_201_CREATED,
)
async def create_visit_note(
    payload: VisitCreateRequest,
    request: Request,
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.DOCTOR, Role.OWNER)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> VisitListItem:
    """Create or update a clinical encounter note (PRD §5.3 F-008, W-009)."""
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Clinic context required.")
    service = VisitService(session)
    return await service.create_or_update_visit_note(
        clinic_id=current_user.clinic_id,
        payload=payload,
        current_user=current_user,
        client_ip=client_ip,
        request_id=request_id,
    )


@router.put(
    "/{visit_id}",
    response_model=VisitListItem,
    status_code=status.HTTP_200_OK,
)
async def update_visit_note(
    visit_id: uuid.UUID,
    payload: VisitUpdateRequest,
    request: Request,
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.DOCTOR, Role.OWNER)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> VisitListItem:
    """Update an existing clinical visit note (PRD §5.3 F-008)."""
    client_ip = request.client.host if request.client else None
    request_id = getattr(request.state, "request_id", None)
    if not current_user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Clinic context required.")
    service = VisitService(session)
    return await service.update_visit_note(
        clinic_id=current_user.clinic_id,
        visit_id=visit_id,
        payload=payload,
        current_user=current_user,
        client_ip=client_ip,
        request_id=request_id,
    )
