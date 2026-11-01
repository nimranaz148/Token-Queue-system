import hashlib
import logging
import secrets
import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import bad_request, forbidden, not_found, unauthorized
from app.models.clinic import Clinic
from app.models.display import DisplayDevice
from app.models.doctor import Doctor
from app.models.token import Token
from app.schemas.audit import AuditAction
from app.schemas.auth import CurrentUser, Role
from app.schemas.display import (
    DisplayDeviceResponse,
    DisplayDoctorFeed,
    DisplayFeedResponse,
    DisplayPairCompleteRequest,
    DisplayPairCompleteResponse,
    DisplayPairInitiateRequest,
    DisplayPairInitiateResponse,
)
from app.services.audit import AuditService

logger = logging.getLogger(__name__)

# In-memory pairing code registry with 10-minute TTL (PRD §5.3 F-020)
_PAIRING_STORE: dict[str, dict] = {}
PAIRING_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def _generate_pairing_code() -> str:
    return "".join(secrets.choice(PAIRING_ALPHABET) for _ in range(6))


class DisplayService:
    """Domain service managing TV display device pairing, feeds, and lifecycle (F-009, F-020)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def initiate_pairing(
        self,
        clinic_id: uuid.UUID,
        payload: DisplayPairInitiateRequest,
        current_user: CurrentUser,
    ) -> DisplayPairInitiateResponse:
        """Generate a 6-character 10-minute pairing code for a waiting room TV (PRD §5.3 F-020)."""
        if current_user.role != Role.OWNER:
            raise forbidden(code="FORBIDDEN", detail="Only clinic owner can pair display devices.")

        # Verify doctors belong to this clinic
        d_stmt = select(Doctor.id).where(
            Doctor.clinic_id == clinic_id,
            Doctor.id.in_(payload.doctor_ids),
            Doctor.active.is_(True),
        )
        d_res = await self.session.execute(d_stmt)
        found_ids = set(d_res.scalars().all())
        if len(found_ids) != len(payload.doctor_ids):
            raise bad_request(
                code="INVALID_DOCTORS",
                detail="One or more selected doctors are invalid or inactive for this clinic.",
            )

        code = _generate_pairing_code()
        expires_at = datetime.now(UTC) + timedelta(minutes=10)

        _PAIRING_STORE[code] = {
            "clinic_id": clinic_id,
            "device_name": payload.device_name.strip(),
            "doctor_ids": [str(d) for d in payload.doctor_ids],
            "expires_at": expires_at,
            "owner_user_id": current_user.user_id,
        }

        return DisplayPairInitiateResponse(
            pairing_code=code,
            expires_at=expires_at,
            device_name=payload.device_name.strip(),
        )

    async def complete_pairing(
        self,
        payload: DisplayPairCompleteRequest,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> DisplayPairCompleteResponse:
        """Validate 6-character code and issue secret device token to the TV screen (F-020)."""
        clean_code = payload.pairing_code.strip().upper()
        entry = _PAIRING_STORE.get(clean_code)

        now = datetime.now(UTC)
        if not entry or entry["expires_at"] < now:
            raise bad_request(
                code="INVALID_PAIRING_CODE",
                detail="Pairing code is invalid or has expired (valid for 10 minutes).",
            )

        clinic_id = entry["clinic_id"]

        # Fetch clinic name
        c_stmt = select(Clinic).where(Clinic.id == clinic_id)
        c_res = await self.session.execute(c_stmt)
        clinic = c_res.scalar_one_or_none()
        if not clinic:
            raise not_found(code="CLINIC_NOT_FOUND", detail="Clinic not found.")

        # Generate long-lived secret device token
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

        device = DisplayDevice(
            id=uuid.uuid4(),
            clinic_id=clinic_id,
            name=entry["device_name"],
            token_hash=token_hash,
            doctor_ids=entry["doctor_ids"],
            paired_at=now,
            revoked_at=None,
        )
        self.session.add(device)
        await self.session.flush()

        AuditService.record_audit(
            session=self.session,
            action=AuditAction.DISPLAY_PAIR,
            entity="display_device",
            entity_id=device.id,
            actor_type="staff",
            actor_id=entry["owner_user_id"],
            clinic_id=clinic_id,
            before=None,
            after={
                "name": device.name,
                "doctor_ids": device.doctor_ids,
            },
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()
        await self.session.refresh(device)

        # Clear used pairing code
        _PAIRING_STORE.pop(clean_code, None)

        return DisplayPairCompleteResponse(
            device_id=device.id,
            device_token=raw_token,
            clinic_id=clinic_id,
            clinic_name=clinic.name,
        )

    async def list_devices(
        self,
        clinic_id: uuid.UUID,
        current_user: CurrentUser,
    ) -> list[DisplayDeviceResponse]:
        """List paired display devices for the clinic owner (PRD §5.3 F-020)."""
        if current_user.role != Role.OWNER:
            raise forbidden(
                code="FORBIDDEN", detail="Only clinic owner can manage display devices."
            )

        stmt = (
            select(DisplayDevice)
            .where(DisplayDevice.clinic_id == clinic_id)
            .order_by(DisplayDevice.paired_at.desc())
        )
        res = await self.session.execute(stmt)
        devices = res.scalars().all()

        results: list[DisplayDeviceResponse] = []
        for d in devices:
            results.append(
                DisplayDeviceResponse(
                    id=d.id,
                    name=d.name,
                    doctor_ids=[str(doc_id) for doc_id in d.doctor_ids],
                    paired_at=d.paired_at,
                    revoked_at=d.revoked_at,
                    is_active=d.revoked_at is None,
                )
            )

        return results

    async def revoke_device(
        self,
        clinic_id: uuid.UUID,
        device_id: uuid.UUID,
        current_user: CurrentUser,
        client_ip: str | None = None,
        request_id: str | None = None,
    ) -> DisplayDeviceResponse:
        """Revoke a display device token immediately (PRD §5.3 F-020)."""
        if current_user.role != Role.OWNER:
            raise forbidden(
                code="FORBIDDEN", detail="Only clinic owner can revoke display devices."
            )

        stmt = select(DisplayDevice).where(
            DisplayDevice.id == device_id,
            DisplayDevice.clinic_id == clinic_id,
        )
        res = await self.session.execute(stmt)
        device = res.scalar_one_or_none()

        if not device:
            raise not_found(code="DEVICE_NOT_FOUND", detail="Display device not found.")

        device.revoked_at = datetime.now(UTC)
        await self.session.flush()

        AuditService.record_audit(
            session=self.session,
            action=AuditAction.DISPLAY_REVOKE,
            entity="display_device",
            entity_id=device.id,
            actor_type="staff",
            actor_id=current_user.user_id,
            clinic_id=clinic_id,
            before={"revoked_at": None},
            after={"revoked_at": str(device.revoked_at)},
            client_ip=client_ip,
            request_id=request_id,
        )

        await self.session.commit()
        await self.session.refresh(device)

        return DisplayDeviceResponse(
            id=device.id,
            name=device.name,
            doctor_ids=[str(doc_id) for doc_id in device.doctor_ids],
            paired_at=device.paired_at,
            revoked_at=device.revoked_at,
            is_active=False,
        )

    async def get_display_feed(
        self,
        device_token: str,
    ) -> DisplayFeedResponse:
        """Retrieve live TV queue feed. Zero patient names or phones (PRD §5.3 F-009, Rule 10)."""
        token_hash = hashlib.sha256(device_token.strip().encode("utf-8")).hexdigest()

        d_stmt = select(DisplayDevice).where(
            DisplayDevice.token_hash == token_hash,
            DisplayDevice.revoked_at.is_(None),
        )
        d_res = await self.session.execute(d_stmt)
        device = d_res.scalar_one_or_none()

        if not device:
            raise unauthorized(
                code="UNAUTHORIZED_DEVICE",
                detail="Display device is not paired or authorization has been revoked.",
            )

        # Get clinic name
        c_stmt = select(Clinic.name).where(Clinic.id == device.clinic_id)
        c_res = await self.session.execute(c_stmt)
        clinic_name = c_res.scalar_one_or_none() or "Clinic"

        # Query assigned doctors
        doc_uuid_list = [uuid.UUID(str(did)) for did in device.doctor_ids]
        doctors_stmt = (
            select(Doctor)
            .where(
                Doctor.clinic_id == device.clinic_id,
                Doctor.id.in_(doc_uuid_list),
            )
            .order_by(Doctor.name.asc())
        )
        doctors_res = await self.session.execute(doctors_stmt)
        doctors = doctors_res.scalars().all()

        today = date.today()
        doctor_feeds: list[DisplayDoctorFeed] = []

        for doc in doctors:
            # Query tokens for today
            t_stmt = (
                select(Token.number, Token.status, Token.position)
                .where(
                    Token.clinic_id == device.clinic_id,
                    Token.doctor_id == doc.id,
                    Token.visit_date == today,
                    Token.status.in_(["serving", "arrived", "booked"]),
                )
                .order_by(Token.position.asc(), Token.number.asc())
            )
            t_res = await self.session.execute(t_stmt)
            token_rows = t_res.all()

            current_num = None
            next_nums: list[int] = []

            for num, status, _ in token_rows:
                if status == "serving" and current_num is None:
                    current_num = num
                elif status in {"arrived", "booked"} and len(next_nums) < 3:
                    next_nums.append(num)

            doctor_feeds.append(
                DisplayDoctorFeed(
                    doctor_id=doc.id,
                    doctor_name=doc.name,
                    specialty=doc.specialty,
                    current_token=current_num,
                    next_tokens=next_nums,
                )
            )

        return DisplayFeedResponse(
            clinic_name=clinic_name,
            doctors=doctor_feeds,
            server_time=datetime.now(UTC),
        )
