import uuid
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.errors import forbidden, unauthorized
from app.core.security import decode_token
from app.schemas.auth import CurrentUser, Role

http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)] = None,
) -> CurrentUser:
    """Extract and validate the current user from Bearer JWT token."""
    if not credentials or not credentials.credentials:
        raise unauthorized(code="UNAUTHORIZED", detail="Missing authentication credentials")

    payload = decode_token(credentials.credentials)

    if payload.get("type") != "access":
        raise unauthorized(code="INVALID_TOKEN", detail="Invalid token type, access token required")

    sub = payload.get("sub")
    if not sub:
        raise unauthorized(code="INVALID_TOKEN", detail="Token subject claim (sub) missing")

    try:
        user_id = uuid.UUID(sub)
    except ValueError:
        raise unauthorized(code="INVALID_TOKEN", detail="Invalid user ID format in token") from None

    email = payload.get("email", "")
    role = payload.get("role", "")
    name = payload.get("name", email.split("@")[0] if "@" in email else "User")
    is_platform_admin = bool(payload.get("is_platform_admin", role == Role.PLATFORM_ADMIN))

    clinic_id: uuid.UUID | None = None
    if payload.get("clinic_id"):
        try:
            clinic_id = uuid.UUID(payload["clinic_id"])
        except ValueError:
            pass

    doctor_id: uuid.UUID | None = None
    if payload.get("doctor_id"):
        try:
            doctor_id = uuid.UUID(payload["doctor_id"])
        except ValueError:
            pass

    return CurrentUser(
        user_id=user_id,
        email=email,
        name=name,
        role=role,
        clinic_id=clinic_id,
        doctor_id=doctor_id,
        is_platform_admin=is_platform_admin,
    )


def require_roles(*allowed_roles: str | Role) -> Callable[..., Any]:
    """Dependency factory that checks if current user possesses one of the allowed roles."""
    expected_roles = {str(r) for r in allowed_roles}

    async def role_checker(
        user: Annotated[CurrentUser, Depends(get_current_user)],
    ) -> CurrentUser:
        if user.role not in expected_roles:
            raise forbidden(
                code="FORBIDDEN",
                detail=f"Role '{user.role}' is not authorized for this action",
            )
        return user

    return role_checker


async def require_platform_admin(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Check if current user is platform admin."""
    if not user.is_platform_admin and user.role != Role.PLATFORM_ADMIN:
        raise forbidden(code="FORBIDDEN", detail="Platform admin privileges required")
    return user


async def require_clinic_member(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> CurrentUser:
    """Ensure the user is assigned to a specific clinic and holds a staff role."""
    if not user.clinic_id:
        raise forbidden(code="CLINIC_REQUIRED", detail="Clinic context required for this action")

    if user.role not in {Role.OWNER, Role.DOCTOR, Role.RECEPTION}:
        raise forbidden(code="FORBIDDEN", detail="User is not an active clinic staff member")

    return user


async def allow_public() -> None:
    """Explicit permission dependency declaring an open/public endpoint."""
    return None
