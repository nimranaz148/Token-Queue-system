from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import allow_public
from app.schemas.ai import (
    PatientChatMessageRead,
    PatientChatRequest,
    PatientChatResponse,
)
from app.schemas.token import (
    PublicClinicInfoResponse,
    SharedVisitAdviceResponse,
    TokenBookingRequest,
    TokenBookingResponse,
    TokenCancelResponse,
    TokenDetailsResponse,
)
from app.services.ai_service import AIService
from app.services.token import TokenService

router = APIRouter(prefix="/public", tags=["public-tokens"])


@router.get(
    "/clinics/{slug}",
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
    "/clinics/{slug}/tokens",
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


@router.get(
    "/tokens/{public_code}",
    response_model=TokenDetailsResponse,
    dependencies=[Depends(allow_public)],
)
async def get_token_details(
    public_code: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenDetailsResponse:
    """Retrieve current token status, wait metrics, and doctor info (PRD F-002, F-003)."""
    service = TokenService(session)
    return await service.get_token_by_public_code(public_code=public_code)


@router.post(
    "/tokens/{public_code}/cancel",
    response_model=TokenCancelResponse,
    dependencies=[Depends(allow_public)],
)
async def cancel_token(
    public_code: str,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> TokenCancelResponse:
    """Cancel a booked or arrived token (PRD F-002, W-005)."""
    service = TokenService(session)
    client_ip = request.client.host if request.client else None
    return await service.cancel_token_by_public_code(
        public_code=public_code,
        reason="Cancelled by patient",
        client_ip=client_ip,
        request_id=idempotency_key,
    )


@router.get(
    "/tokens/{public_code}/advice",
    response_model=SharedVisitAdviceResponse,
    dependencies=[Depends(allow_public)],
    status_code=status.HTTP_200_OK,
)
async def get_shared_visit_advice(
    public_code: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SharedVisitAdviceResponse:
    """Retrieve shared doctor prescription advice if clinic and visit sharing are enabled (F-021)."""
    service = TokenService(session)
    return await service.get_shared_visit_advice(public_code=public_code)


@router.get(
    "/tokens/{public_code}/chat",
    response_model=list[PatientChatMessageRead],
    dependencies=[Depends(allow_public)],
    status_code=status.HTTP_200_OK,
)
async def get_patient_chat_history(
    public_code: str,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[PatientChatMessageRead]:
    """Retrieve chat message history for this token session (F-019)."""
    service = AIService(session)
    _, messages = await service.get_patient_chat_history(public_code=public_code)
    return [PatientChatMessageRead.model_validate(m) for m in messages]


@router.post(
    "/tokens/{public_code}/chat",
    response_model=PatientChatResponse,
    dependencies=[Depends(allow_public)],
    status_code=status.HTTP_200_OK,
)
async def send_patient_chat_message(
    public_code: str,
    payload: PatientChatRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> PatientChatResponse:
    """Send a message to the patient queue assistant (F-019). Answers queue & clinic questions; refuses medical advice."""
    service = AIService(session)
    reply, tool_calls = await service.send_patient_message(
        public_code=public_code,
        message=payload.message,
    )
    return PatientChatResponse(reply=reply, tool_calls=tool_calls)

