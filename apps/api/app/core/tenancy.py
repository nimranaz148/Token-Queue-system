import contextlib
import contextvars
import uuid
from collections.abc import AsyncGenerator, Generator
from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import event, false
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria

from app.core.database import get_db
from app.core.errors import forbidden
from app.core.permissions import get_current_user
from app.models.base import Base
from app.models.clinic import Clinic
from app.schemas.auth import CurrentUser

# Context variable tracking the current active tenant (clinic_id)
_current_tenant_id: contextvars.ContextVar[uuid.UUID | None] = contextvars.ContextVar(
    "current_tenant_id", default=None
)

# Context variable tracking whether tenancy enforcement is bypassed (e.g. platform admin)
_bypass_scope: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "bypass_tenant_scope", default=False
)


def get_current_tenant_id() -> uuid.UUID | None:
    """Return the active tenant clinic ID from context."""
    return _current_tenant_id.get()


def set_current_tenant_id(
    clinic_id: uuid.UUID | None,
) -> contextvars.Token[uuid.UUID | None]:
    """Set the active tenant clinic ID in context."""
    return _current_tenant_id.set(clinic_id)


def reset_current_tenant_id(token: contextvars.Token[uuid.UUID | None]) -> None:
    """Reset the tenant context variable to its previous state."""
    _current_tenant_id.reset(token)


def is_scope_bypassed() -> bool:
    """Check if tenant scoping is currently bypassed."""
    return _bypass_scope.get()


def set_bypass_scope(bypass: bool) -> contextvars.Token[bool]:
    """Set the tenant bypass flag in context."""
    return _bypass_scope.set(bypass)


def reset_bypass_scope(token: contextvars.Token[bool]) -> None:
    """Reset the tenant bypass context variable."""
    _bypass_scope.reset(token)


@contextlib.contextmanager
def tenant_scope(
    clinic_id: uuid.UUID | None,
    bypass: bool = False,
) -> Generator[None, None, None]:
    """Context manager for synchronously setting tenant scope."""
    tenant_token = set_current_tenant_id(clinic_id)
    bypass_token = set_bypass_scope(bypass)
    try:
        yield
    finally:
        reset_current_tenant_id(tenant_token)
        reset_bypass_scope(bypass_token)


@contextlib.asynccontextmanager
async def async_tenant_scope(
    clinic_id: uuid.UUID | None,
    bypass: bool = False,
) -> AsyncGenerator[None, None]:
    """Context manager for asynchronously setting tenant scope."""
    tenant_token = set_current_tenant_id(clinic_id)
    bypass_token = set_bypass_scope(bypass)
    try:
        yield
    finally:
        reset_current_tenant_id(tenant_token)
        reset_bypass_scope(bypass_token)


@event.listens_for(Session, "do_orm_execute")
def _apply_tenant_query_scope(orm_execute_state: ORMExecuteState) -> None:
    """Automatically append tenant scoping criteria to ORM SELECT queries."""
    if orm_execute_state.is_select:
        if is_scope_bypassed():
            return

        clinic_id = get_current_tenant_id()

        def _criteria(cls: type[Any]) -> Any:
            if cls is Clinic:
                if clinic_id is not None:
                    return cls.id == clinic_id
                return false()
            if hasattr(cls, "clinic_id"):
                if clinic_id is not None:
                    return cls.clinic_id == clinic_id
                return false()
            return True

        orm_execute_state.statement = orm_execute_state.statement.options(
            with_loader_criteria(
                Base,
                _criteria,
                include_aliases=True,
                track_closure_variables=False,
            )
        )


@event.listens_for(Session, "before_flush")
def _enforce_tenant_on_flush(session: Session, flush_context: Any, instances: Any) -> None:
    """Enforce tenant scoping on ORM insert, update, and delete actions."""
    if is_scope_bypassed():
        return

    clinic_id = get_current_tenant_id()

    # 1. Enforce on newly added instances
    for obj in session.new:
        if hasattr(obj, "clinic_id") and obj.__class__ is not Clinic:
            if clinic_id is None:
                raise forbidden(
                    code="TENANT_REQUIRED",
                    detail=f"Cannot persist {type(obj).__name__} without tenant context",
                )
            target_cid = obj.clinic_id
            if target_cid is None:
                obj.clinic_id = clinic_id
            elif target_cid != clinic_id:
                raise forbidden(
                    code="CROSS_TENANT_ACCESS",
                    detail=f"Cannot persist {type(obj).__name__} for a different clinic",
                )

    # 2. Enforce on modified instances
    for obj in session.dirty:
        if hasattr(obj, "clinic_id") and obj.__class__ is not Clinic:
            if clinic_id is None:
                raise forbidden(
                    code="TENANT_REQUIRED",
                    detail=f"Cannot modify {type(obj).__name__} without tenant context",
                )
            target_cid = obj.clinic_id
            if target_cid != clinic_id:
                raise forbidden(
                    code="CROSS_TENANT_ACCESS",
                    detail=f"Cannot modify {type(obj).__name__} belonging to a different clinic",
                )

    # 3. Enforce on deleted instances
    for obj in session.deleted:
        if hasattr(obj, "clinic_id") and obj.__class__ is not Clinic:
            if clinic_id is None:
                raise forbidden(
                    code="TENANT_REQUIRED",
                    detail=f"Cannot delete {type(obj).__name__} without tenant context",
                )
            target_cid = obj.clinic_id
            if target_cid != clinic_id:
                raise forbidden(
                    code="CROSS_TENANT_ACCESS",
                    detail=f"Cannot delete {type(obj).__name__} belonging to a different clinic",
                )


async def get_scoped_db(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a tenant-scoped database session for staff."""
    token = set_current_tenant_id(current_user.clinic_id)
    bypass_token = set_bypass_scope(current_user.is_platform_admin)
    try:
        yield session
    finally:
        reset_current_tenant_id(token)
        reset_bypass_scope(bypass_token)
