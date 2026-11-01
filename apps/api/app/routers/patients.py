import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import require_roles
from app.schemas.auth import CurrentUser, Role
from app.schemas.patient import (
    PatientDetailResponse,
    PatientSearchResult,
    PatientUpdateRequest,
)
from app.services.patient import PatientService

router = APIRouter(prefix="/patients", tags=["Patients (F-006)"])


@router.get("", response_model=list[PatientSearchResult])
async def search_patients(
    query: Annotated[str, Query(description="Search by name or phone (>= 2 chars)")],
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.RECEPTION, Role.OWNER, Role.DOCTOR)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[PatientSearchResult]:
    """Search registered patients by name or phone within the clinic (PRD §5.3 F-006)."""
    service = PatientService(session)
    return await service.search_patients(query=query, current_user=current_user)


@router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient_profile(
    patient_id: uuid.UUID,
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.RECEPTION, Role.OWNER, Role.DOCTOR)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PatientDetailResponse:
    """Retrieve full patient profile, notes, and visit history count (PRD §5.3 F-006)."""
    service = PatientService(session)
    return await service.get_patient_profile(patient_id=patient_id, current_user=current_user)


@router.put("/{patient_id}", response_model=PatientDetailResponse)
async def update_patient_profile(
    patient_id: uuid.UUID,
    request: PatientUpdateRequest,
    current_user: Annotated[
        CurrentUser,
        Depends(require_roles(Role.RECEPTION, Role.OWNER)),
    ],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PatientDetailResponse:
    """Update patient personal details and clinical notes with audit log (PRD §5.3 F-006)."""
    service = PatientService(session)
    return await service.update_patient_profile(
        patient_id=patient_id,
        data=request,
        current_user=current_user,
    )
