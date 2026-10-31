import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.core.masking import hash_ip, mask_sensitive_data
from app.core.tenancy import get_current_tenant_id
from app.models.audit import AuditLog
from app.schemas.audit import AuditAction


class AuditService:
    """Domain service managing the creation and retrieval of immutable audit logs."""

    @staticmethod
    def record_audit(
        session: AsyncSession | Session,
        action: str | AuditAction,
        entity: str,
        entity_id: uuid.UUID | None = None,
        actor_type: str = "staff",
        actor_id: uuid.UUID | None = None,
        clinic_id: uuid.UUID | None = None,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        request_id: str | None = None,
        client_ip: str | None = None,
    ) -> AuditLog:
        """Create and add a masked audit log entry to the active database session."""
        effective_clinic_id = clinic_id if clinic_id is not None else get_current_tenant_id()

        masked_before = mask_sensitive_data(before)
        masked_after = mask_sensitive_data(after)
        ip_hash = hash_ip(client_ip)

        audit_entry = AuditLog(
            clinic_id=effective_clinic_id,
            actor_type=str(actor_type),
            actor_id=actor_id,
            action=str(action),
            entity=entity,
            entity_id=entity_id,
            before=masked_before,
            after=masked_after,
            request_id=request_id,
            ip_hash=ip_hash,
        )

        session.add(audit_entry)
        return audit_entry

    @staticmethod
    async def list_audit_logs(
        session: AsyncSession,
        entity: str | None = None,
        action: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditLog]:
        """Query audit trail records with optional entity and action filtering."""
        stmt = select(AuditLog).order_by(AuditLog.at.desc()).limit(limit).offset(offset)
        if entity:
            stmt = stmt.where(AuditLog.entity == entity)
        if action:
            stmt = stmt.where(AuditLog.action == action)

        res = await session.execute(stmt)
        return list(res.scalars().all())
