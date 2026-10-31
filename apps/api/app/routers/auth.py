from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.permissions import (
    get_current_user,
    require_platform_admin,
    require_roles,
)
from app.schemas.auth import (
    CurrentUser,
    LoginRequest,
    RefreshRequest,
    Role,
    TokenResponse,
    UserResponse,
)
from app.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

owner_permission = require_roles(Role.OWNER)
doctor_permission = require_roles(Role.DOCTOR, Role.OWNER)
reception_permission = require_roles(Role.RECEPTION, Role.OWNER)


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Authenticate staff member or platform admin and return access/refresh tokens."""
    user = await AuthService.authenticate_user(
        session=session,
        email=req.email,
        password=req.password,
        clinic_id=req.clinic_id,
    )
    return AuthService.issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    req: RefreshRequest,
) -> TokenResponse:
    """Refresh JWT tokens using a valid refresh token."""
    return AuthService.refresh_tokens(req.refresh_token)


@router.post("/logout")
async def logout(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, str]:
    """Logout current user session."""
    return AuthService.logout(current_user)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> UserResponse:
    """Get authenticated user profile and permissions."""
    return UserResponse.model_validate(current_user)


# Test role endpoints to verify PRD §14.2 permission matrix
@router.get("/test/platform-admin", response_model=dict[str, Any])
async def test_platform_admin_access(
    current_user: Annotated[CurrentUser, Depends(require_platform_admin)],
) -> dict[str, Any]:
    """Protected endpoint requiring platform_admin role."""
    return {"message": "Welcome platform admin", "role": current_user.role}


@router.get("/test/owner", response_model=dict[str, Any])
async def test_owner_access(
    current_user: Annotated[CurrentUser, Depends(owner_permission)],
) -> dict[str, Any]:
    """Protected endpoint requiring owner role."""
    return {"message": "Welcome owner", "role": current_user.role}


@router.get("/test/doctor", response_model=dict[str, Any])
async def test_doctor_access(
    current_user: Annotated[CurrentUser, Depends(doctor_permission)],
) -> dict[str, Any]:
    """Protected endpoint requiring doctor or owner role."""
    return {"message": "Welcome doctor", "role": current_user.role}


@router.get("/test/reception", response_model=dict[str, Any])
async def test_reception_access(
    current_user: Annotated[CurrentUser, Depends(reception_permission)],
) -> dict[str, Any]:
    """Protected endpoint requiring reception or owner role."""
    return {"message": "Welcome reception", "role": current_user.role}
