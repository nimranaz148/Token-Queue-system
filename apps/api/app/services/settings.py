import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import conflict, forbidden, not_found
from app.models.clinic import Clinic, ClinicSettings
from app.schemas.audit import AuditAction
from app.schemas.auth import CurrentUser, Role
from app.schemas.settings import ClinicSettingsRead, ClinicSettingsUpdate
from app.services.audit import AuditService


class SettingsService:
    """Domain service managing operational settings for clinic tenants (PRD §5.3 F-011)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_settings(
        self,
        clinic_id: uuid.UUID,
        current_user: CurrentUser,
    ) -> ClinicSettingsRead:
        """Retrieve operational settings and clinic profile (F-011)."""
        if current_user.role not in {Role.OWNER, Role.PLATFORM_ADMIN}:
            raise forbidden(code="FORBIDDEN", detail="Only clinic owner can access settings.")

        stmt = (
            select(Clinic, ClinicSettings)
            .join(ClinicSettings, Clinic.id == ClinicSettings.clinic_id)
            .where(Clinic.id == clinic_id)
        )
        res = await self.session.execute(stmt)
        row = res.first()
        if not row:
            raise not_found(
                code="SETTINGS_NOT_FOUND",
                detail=f"Settings for clinic {clinic_id} not found.",
            )

        clinic, settings = row

        return ClinicSettingsRead(
            clinic_id=clinic.id,
            clinic_name=clinic.name,
            slug=clinic.slug,
            time_zone=clinic.time_zone or "Asia/Karachi",
            address=clinic.address,
            phone=clinic.phone,
            maps_url=clinic.maps_url,
            logo_path=clinic.logo_path,
            online_booking_enabled=settings.online_booking_enabled
            if settings.online_booking_enabled is not None
            else True,
            daily_online_limit=settings.daily_online_limit or 50,
            advance_days=settings.advance_days if settings.advance_days is not None else 1,
            default_consult_minutes=settings.default_consult_minutes or 10,
            call_only_arrived=bool(settings.call_only_arrived),
            language_default=settings.language_default or "en",
            share_advice_with_patient=bool(settings.share_advice_with_patient),
            ai_notes_enabled=bool(settings.ai_notes_enabled),
            ai_consent_accepted_by=settings.ai_consent_accepted_by,
            ai_consent_accepted_at=settings.ai_consent_accepted_at,
            version=settings.version or 1,
            updated_at=settings.updated_at or datetime.now(UTC),
        )

    async def update_settings(
        self,
        clinic_id: uuid.UUID,
        payload: ClinicSettingsUpdate,
        current_user: CurrentUser,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> ClinicSettingsRead:
        """Update clinic operational settings with optimistic locking and audit logging (F-011)."""
        if current_user.role not in {Role.OWNER, Role.PLATFORM_ADMIN}:
            raise forbidden(code="FORBIDDEN", detail="Only clinic owner can modify settings.")

        stmt = (
            select(Clinic, ClinicSettings)
            .join(ClinicSettings, Clinic.id == ClinicSettings.clinic_id)
            .where(Clinic.id == clinic_id)
        )
        res = await self.session.execute(stmt)
        row = res.first()
        if not row:
            raise not_found(
                code="SETTINGS_NOT_FOUND",
                detail=f"Settings for clinic {clinic_id} not found.",
            )

        clinic, settings = row

        # Optimistic concurrency check (PRD §11)
        if settings.version != payload.version:
            raise conflict(
                code="SETTINGS_VERSION_CONFLICT",
                detail=f"Settings have been modified by another transaction. Expected version {settings.version}, got {payload.version}.",
            )

        before_state = {
            "clinic_name": clinic.name,
            "time_zone": clinic.time_zone,
            "address": clinic.address,
            "phone": clinic.phone,
            "maps_url": clinic.maps_url,
            "logo_path": clinic.logo_path,
            "online_booking_enabled": settings.online_booking_enabled,
            "daily_online_limit": settings.daily_online_limit,
            "advance_days": settings.advance_days,
            "default_consult_minutes": settings.default_consult_minutes,
            "call_only_arrived": settings.call_only_arrived,
            "language_default": settings.language_default,
            "share_advice_with_patient": settings.share_advice_with_patient,
            "ai_notes_enabled": settings.ai_notes_enabled,
            "version": settings.version,
        }

        # Update clinic profile fields
        if payload.clinic_name is not None:
            clinic.name = payload.clinic_name
        if payload.time_zone is not None:
            clinic.time_zone = payload.time_zone
        if payload.address is not None:
            clinic.address = payload.address
        if payload.phone is not None:
            clinic.phone = payload.phone
        if payload.maps_url is not None:
            clinic.maps_url = payload.maps_url
        if payload.logo_path is not None:
            clinic.logo_path = payload.logo_path

        # Update settings fields
        if payload.online_booking_enabled is not None:
            settings.online_booking_enabled = payload.online_booking_enabled
        if payload.daily_online_limit is not None:
            settings.daily_online_limit = payload.daily_online_limit
        if payload.advance_days is not None:
            settings.advance_days = payload.advance_days
        if payload.default_consult_minutes is not None:
            settings.default_consult_minutes = payload.default_consult_minutes
        if payload.call_only_arrived is not None:
            settings.call_only_arrived = payload.call_only_arrived
        if payload.language_default is not None:
            settings.language_default = payload.language_default
        if payload.share_advice_with_patient is not None:
            settings.share_advice_with_patient = payload.share_advice_with_patient

        # AI notes consent handling (PRD §5.3 F-011 / Q-004)
        if payload.ai_notes_enabled is not None:
            if payload.ai_notes_enabled and not settings.ai_notes_enabled:
                settings.ai_consent_accepted_by = current_user.user_id
                settings.ai_consent_accepted_at = datetime.now(UTC)
            elif not payload.ai_notes_enabled:
                settings.ai_consent_accepted_by = None
                settings.ai_consent_accepted_at = None
            settings.ai_notes_enabled = payload.ai_notes_enabled

        # Concurrency version increment
        settings.version += 1
        settings.updated_at = datetime.now(UTC)

        after_state = {
            "clinic_name": clinic.name,
            "time_zone": clinic.time_zone,
            "address": clinic.address,
            "phone": clinic.phone,
            "maps_url": clinic.maps_url,
            "logo_path": clinic.logo_path,
            "online_booking_enabled": settings.online_booking_enabled,
            "daily_online_limit": settings.daily_online_limit,
            "advance_days": settings.advance_days,
            "default_consult_minutes": settings.default_consult_minutes,
            "call_only_arrived": settings.call_only_arrived,
            "language_default": settings.language_default,
            "share_advice_with_patient": settings.share_advice_with_patient,
            "ai_notes_enabled": settings.ai_notes_enabled,
            "version": settings.version,
        }

        # Immutable audit logging (PRD §14.1)
        AuditService.record_audit(
            session=self.session,
            action=AuditAction.SETTINGS_CHANGE,
            entity="clinic_settings",
            entity_id=clinic.id,
            actor_type="staff",
            actor_id=current_user.user_id,
            clinic_id=clinic.id,
            before=before_state,
            after=after_state,
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()

        return ClinicSettingsRead(
            clinic_id=clinic.id,
            clinic_name=clinic.name,
            slug=clinic.slug,
            time_zone=clinic.time_zone or "Asia/Karachi",
            address=clinic.address,
            phone=clinic.phone,
            maps_url=clinic.maps_url,
            logo_path=clinic.logo_path,
            online_booking_enabled=settings.online_booking_enabled
            if settings.online_booking_enabled is not None
            else True,
            daily_online_limit=settings.daily_online_limit or 50,
            advance_days=settings.advance_days if settings.advance_days is not None else 1,
            default_consult_minutes=settings.default_consult_minutes or 10,
            call_only_arrived=bool(settings.call_only_arrived),
            language_default=settings.language_default or "en",
            share_advice_with_patient=bool(settings.share_advice_with_patient),
            ai_notes_enabled=bool(settings.ai_notes_enabled),
            ai_consent_accepted_by=settings.ai_consent_accepted_by,
            ai_consent_accepted_at=settings.ai_consent_accepted_at,
            version=settings.version or 1,
            updated_at=settings.updated_at or datetime.now(UTC),
        )
