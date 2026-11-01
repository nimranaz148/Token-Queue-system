from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import allow_public
from app.schemas.token import (
    PublicClinicInfoResponse,
    TokenBookingRequest,
    TokenBookingResponse,
)
from app.services.token import TokenService

router = APIRouter(prefix="/public/clinics", tags=["public-tokens"])


@router.get(
    "/{slug}",
    response_model=PublicClinicInfoResponse,
    dependencies=[Depends(allow_public)],
)
async def get_public_clinic_details(
    slug: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PublicClinicInfoResponse:
    """Retrieve public clinic profile, active OPD doctors, and schedule availability (PRD F-001)."""
    service = TokenService(session)
    return await service.get_public_clinic_info(slug=slug)


@router.post(
    "/{slug}/tokens",
    response_model=TokenBookingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(allow_public)],
)
async def book_token(
    slug: str,
    payload: TokenBookingRequest,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TokenBookingResponse:
    """Book a new OPD patient token online with Turnstile verification and atomic numbering (PRD F-001, W-001)."""
    service = TokenService(session)
    client_ip = request.client.host if request.client else None
    return await service.book_token(
        slug=slug,
        payload=payload,
        client_ip=client_ip,
        request_id=idempotency_key,
    )
