import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import conflict, not_found, unprocessable_entity
from app.core.tenancy import async_tenant_scope
from app.models.doctor import Doctor
from app.models.member import ClinicMember
from app.schemas.audit import AuditAction
from app.schemas.auth import CurrentUser
from app.schemas.member import MemberInviteRequest, MemberRole, MemberUpdateRequest
from app.services.audit import AuditService


class MemberService:
    """Domain service for clinic staff management (PRD §5.3 F-015, §14.1, §14.2)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_members(self, clinic_id: uuid.UUID) -> tuple[list[dict[str, Any]], int]:
        """List all active and inactive staff members for the given clinic."""
        async with async_tenant_scope(clinic_id):
            stmt = (
                select(ClinicMember, Doctor.name.label("doctor_name"))
                .outerjoin(Doctor, ClinicMember.doctor_id == Doctor.id)
                .where(ClinicMember.deleted_at.is_(None))
                .order_by(ClinicMember.created_at.asc())
            )
            result = await self.session.execute(stmt)
            rows = result.all()

            items: list[dict[str, Any]] = []
            for member, doc_name in rows:
                items.append(
                    {
                        "id": member.id,
                        "clinic_id": member.clinic_id,
                        "user_id": member.user_id,
                        "name": member.name,
                        "email": member.email,
                        "phone": member.phone,
                        "role": member.role,
                        "doctor_id": member.doctor_id,
                        "doctor_name": doc_name,
                        "active": member.active,
                        "created_at": member.created_at,
                        "updated_at": member.updated_at,
                    }
                )
            return items, len(items)

    async def invite_member(
        self,
        clinic_id: uuid.UUID,
        current_user: CurrentUser,
        data: MemberInviteRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """Invite/create a staff member and record member.invite audit log."""
        async with async_tenant_scope(clinic_id):
            normalized_email = str(data.email).lower().strip()

            # Check if email is already in this clinic
            existing_stmt = select(ClinicMember).where(
                ClinicMember.email == normalized_email,
                ClinicMember.deleted_at.is_(None),
            )
            existing_res = await self.session.execute(existing_stmt)
            if existing_res.scalar_one_or_none() is not None:
                raise conflict(
                    code="EMAIL_ALREADY_MEMBER",
                    detail=f"Staff member with email '{data.email}' already exists in this clinic",
                )

            doctor_name: str | None = None
            assigned_doctor_id: uuid.UUID | None = None

            if data.role == MemberRole.DOCTOR:
                if not data.doctor_id:
                    raise unprocessable_entity(
                        code="DOCTOR_ID_REQUIRED",
                        detail="linked_doctor_id is required when role is doctor",
                    )
                doc_stmt = select(Doctor).where(
                    Doctor.id == data.doctor_id,
                    Doctor.deleted_at.is_(None),
                )
                doc_res = await self.session.execute(doc_stmt)
                doc = doc_res.scalar_one_or_none()
                if not doc:
                    raise not_found(
                        code="DOCTOR_NOT_FOUND",
                        detail=f"Doctor with ID '{data.doctor_id}' not found in this clinic",
                    )
                assigned_doctor_id = doc.id
                doctor_name = doc.name
            else:
                assigned_doctor_id = None

            now = datetime.now(UTC)
            member = ClinicMember(
                id=uuid.uuid4(),
                clinic_id=clinic_id,
                user_id=uuid.uuid4(),  # placeholder until first magic link login
                name=data.name.strip(),
                email=normalized_email,
                phone=data.phone.strip() if data.phone else None,
                role=data.role.value,
                doctor_id=assigned_doctor_id,
                active=True,
                created_at=now,
                updated_at=now,
            )
            self.session.add(member)
            await self.session.flush()

            AuditService.record_audit(
                session=self.session,
                action=AuditAction.MEMBER_INVITE,
                entity="member",
                entity_id=member.id,
                actor_type=current_user.role,
                actor_id=current_user.user_id,
                clinic_id=clinic_id,
                after={
                    "member_id": str(member.id),
                    "name": member.name,
                    "email": member.email,
                    "role": member.role,
                    "doctor_id": str(member.doctor_id) if member.doctor_id else None,
                },
                client_ip=ip_address,
            )

            await self.session.commit()
            await self.session.refresh(member)

            return {
                "id": member.id,
                "clinic_id": member.clinic_id,
                "user_id": member.user_id,
                "name": member.name,
                "email": member.email,
                "phone": member.phone,
                "role": member.role,
                "doctor_id": member.doctor_id,
                "doctor_name": doctor_name,
                "active": member.active,
                "created_at": member.created_at,
                "updated_at": member.updated_at,
            }

    async def update_member(
        self,
        clinic_id: uuid.UUID,
        member_id: uuid.UUID,
        current_user: CurrentUser,
        data: MemberUpdateRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """Update role, linked doctor, or status with audit logs."""
        async with async_tenant_scope(clinic_id):
            stmt = select(ClinicMember).where(
                ClinicMember.id == member_id,
                ClinicMember.deleted_at.is_(None),
            )
            res = await self.session.execute(stmt)
            member = res.scalar_one_or_none()
            if not member:
                raise not_found(
                    code="MEMBER_NOT_FOUND",
                    detail=f"Staff member with ID '{member_id}' not found",
                )

            old_role = member.role
            old_active = member.active

            if data.name is not None:
                member.name = data.name.strip()
            if data.phone is not None:
                member.phone = data.phone.strip() if data.phone else None

            role_changed = False
            if data.role is not None and data.role.value != old_role:
                role_changed = True
                member.role = data.role.value

            # Validate doctor link if role is or became doctor
            if member.role == MemberRole.DOCTOR.value:
                target_doctor_id = (
                    data.doctor_id if data.doctor_id is not None else member.doctor_id
                )
                if not target_doctor_id:
                    raise unprocessable_entity(
                        code="DOCTOR_ID_REQUIRED",
                        detail="linked_doctor_id is required when role is doctor",
                    )
                doc_stmt = select(Doctor).where(
                    Doctor.id == target_doctor_id,
                    Doctor.deleted_at.is_(None),
                )
                doc_res = await self.session.execute(doc_stmt)
                doc = doc_res.scalar_one_or_none()
                if not doc:
                    raise not_found(
                        code="DOCTOR_NOT_FOUND",
                        detail=f"Doctor with ID '{target_doctor_id}' not found in this clinic",
                    )
                if member.doctor_id != target_doctor_id:
                    role_changed = True
                    member.doctor_id = target_doctor_id
            else:
                if member.doctor_id is not None:
                    role_changed = True
                    member.doctor_id = None

            deactivated = False
            if data.active is not None:
                if old_active and not data.active:
                    deactivated = True
                member.active = data.active

            member.updated_at = datetime.now(UTC)
            self.session.add(member)
            await self.session.flush()

            if role_changed:
                AuditService.record_audit(
                    session=self.session,
                    action=AuditAction.MEMBER_ROLE_CHANGE,
                    entity="member",
                    entity_id=member.id,
                    actor_type=current_user.role,
                    actor_id=current_user.user_id,
                    clinic_id=clinic_id,
                    before={"role": old_role},
                    after={
                        "member_id": str(member.id),
                        "role": member.role,
                        "doctor_id": str(member.doctor_id) if member.doctor_id else None,
                    },
                    client_ip=ip_address,
                )

            if deactivated:
                AuditService.record_audit(
                    session=self.session,
                    action=AuditAction.MEMBER_DEACTIVATE,
                    entity="member",
                    entity_id=member.id,
                    actor_type=current_user.role,
                    actor_id=current_user.user_id,
                    clinic_id=clinic_id,
                    before={"active": True},
                    after={
                        "member_id": str(member.id),
                        "email": member.email,
                        "active": False,
                    },
                    client_ip=ip_address,
                )

            await self.session.commit()
            await self.session.refresh(member)

            doctor_name = None
            if member.doctor_id:
                doc_name_stmt = select(Doctor.name).where(Doctor.id == member.doctor_id)
                doc_name_res = await self.session.execute(doc_name_stmt)
                doctor_name = doc_name_res.scalar_one_or_none()

            return {
                "id": member.id,
                "clinic_id": member.clinic_id,
                "user_id": member.user_id,
                "name": member.name,
                "email": member.email,
                "phone": member.phone,
                "role": member.role,
                "doctor_id": member.doctor_id,
                "doctor_name": doctor_name,
                "active": member.active,
                "created_at": member.created_at,
                "updated_at": member.updated_at,
            }
