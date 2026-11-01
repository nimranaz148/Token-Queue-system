import logging
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import not_found
from app.integrations.realtime import SupabaseRealtimeClient
from app.models.clinic import Clinic
from app.models.doctor import Doctor, DoctorSchedule
from app.models.stats import DailyStats
from app.models.token import Token, TokenEvent
from app.schemas.audit import AuditAction
from app.schemas.jobs import (
    ClinicDayCloseResult,
    DailyBriefJobResponse,
    DayCloseResponse,
    DoctorStatsSummary,
)
from app.services.audit import AuditService

logger = logging.getLogger(__name__)


class JobsService:
    """Service implementing background jobs: Day Close (W-006) and metrics aggregation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def run_day_close(
        self,
        clinic_id: uuid.UUID | None = None,
        target_date: date | None = None,
        force: bool = False,
    ) -> DayCloseResponse:
        """Execute automated or on-demand Day Close (W-006).

        1. Identifies clinics past OPD end + 60 min (or forced/specified).
        2. Transitions booked, arrived, skipped, hold -> no_show.
        3. Transitions serving -> done.
        4. Writes token_events and immutable audit logs.
        5. Computes and upserts daily KPI metrics into daily_stats.
        6. Idempotent per clinic + date.
        """
        if clinic_id:
            stmt = select(Clinic).where(Clinic.id == clinic_id)
            res = await self.session.execute(stmt)
            clinic = res.scalar_one_or_none()
            if not clinic:
                raise not_found(code="CLINIC_NOT_FOUND", detail=f"Clinic {clinic_id} not found.")
            clinics = [clinic]
        else:
            stmt = select(Clinic).where(Clinic.status.in_(["active", "trial"]))
            res = await self.session.execute(stmt)
            clinics = list(res.scalars().all())

        results: list[ClinicDayCloseResult] = []

        for clinic in clinics:
            # Determine timezone and local time
            try:
                zone = ZoneInfo(clinic.time_zone)
            except Exception:
                zone = ZoneInfo("Asia/Karachi")

            local_now = datetime.now(zone)
            effective_date = target_date if target_date is not None else local_now.date()

            # Schedule cutoff check for automated runs
            if clinic_id is None and not force:
                sched_stmt = (
                    select(DoctorSchedule)
                    .join(Doctor, DoctorSchedule.doctor_id == Doctor.id)
                    .where(
                        Doctor.clinic_id == clinic.id,
                        DoctorSchedule.weekday == effective_date.weekday(),
                    )
                )
                sched_res = await self.session.execute(sched_stmt)
                schedules = list(sched_res.scalars().all())

                if schedules:
                    latest_end = max(s.end_time for s in schedules)
                    if effective_date == local_now.date():
                        cutoff_time = datetime.combine(
                            effective_date, latest_end, tzinfo=zone
                        ) + timedelta(minutes=60)
                        if local_now < cutoff_time:
                            # Clinic has not reached OPD end + 60 min yet
                            continue
                else:
                    # No schedule for today: only close if past date or near midnight (>=23:00)
                    if effective_date == local_now.date() and local_now.hour < 23:
                        continue

            # Process tokens for this clinic and effective date
            tok_stmt = select(Token).where(
                Token.clinic_id == clinic.id,
                Token.visit_date == effective_date,
            )
            tok_res = await self.session.execute(tok_stmt)
            tokens = list(tok_res.scalars().all())

            tokens_no_show = 0
            tokens_done = 0
            now_utc = datetime.now(UTC)

            for token in tokens:
                if token.status in ("booked", "arrived", "skipped", "hold"):
                    old_status = token.status
                    token.status = "no_show"
                    tokens_no_show += 1

                    self.session.add(
                        TokenEvent(
                            clinic_id=clinic.id,
                            token_id=token.id,
                            from_status=old_status,
                            to_status="no_show",
                            actor_type="system",
                            actor_id=None,
                            at=now_utc,
                        )
                    )
                    AuditService.record_audit(
                        session=self.session,
                        action=AuditAction.TOKEN_NO_SHOW,
                        entity="token",
                        entity_id=token.id,
                        actor_type="system",
                        clinic_id=clinic.id,
                        before={"status": old_status},
                        after={"status": "no_show"},
                    )

                elif token.status == "serving":
                    old_status = token.status
                    token.status = "done"
                    if not token.completed_at:
                        token.completed_at = now_utc
                    tokens_done += 1

                    self.session.add(
                        TokenEvent(
                            clinic_id=clinic.id,
                            token_id=token.id,
                            from_status="serving",
                            to_status="done",
                            actor_type="system",
                            actor_id=None,
                            at=now_utc,
                        )
                    )
                    AuditService.record_audit(
                        session=self.session,
                        action=AuditAction.TOKEN_NEXT,
                        entity="token",
                        entity_id=token.id,
                        actor_type="system",
                        clinic_id=clinic.id,
                        before={"status": old_status},
                        after={"status": "done"},
                    )

            # Calculate and upsert daily_stats per doctor
            # Group tokens by doctor
            doc_stmt = select(Doctor).where(Doctor.clinic_id == clinic.id)
            doc_res = await self.session.execute(doc_stmt)
            doctors = list(doc_res.scalars().all())

            # Map doctor id to tokens
            doctor_tokens: dict[uuid.UUID, list[Token]] = {doc.id: [] for doc in doctors}
            for token in tokens:
                if token.doctor_id in doctor_tokens:
                    doctor_tokens[token.doctor_id].append(token)
                else:
                    doctor_tokens[token.doctor_id] = [token]

            clinic_stats: list[DoctorStatsSummary] = []

            for doc_id, doc_toks in doctor_tokens.items():
                seen = sum(1 for t in doc_toks if t.status == "done")
                no_shows = sum(1 for t in doc_toks if t.status == "no_show")
                cancelled = sum(1 for t in doc_toks if t.status == "cancelled")
                online_count = sum(1 for t in doc_toks if t.source == "online")
                walk_in_count = sum(1 for t in doc_toks if t.source == "walk_in")

                # Wait times in minutes
                wait_seconds: list[float] = []
                for t in doc_toks:
                    if t.called_at and t.arrived_at:
                        diff = (t.called_at - t.arrived_at).total_seconds()
                        if diff >= 0:
                            wait_seconds.append(diff)
                    elif t.called_at and t.created_at:
                        diff = (t.called_at - t.created_at).total_seconds()
                        if diff >= 0:
                            wait_seconds.append(diff)

                avg_wait = (
                    Decimal(f"{sum(wait_seconds) / len(wait_seconds) / 60.0:.2f}")
                    if wait_seconds
                    else None
                )

                # Consult times in minutes
                consult_seconds: list[float] = []
                for t in doc_toks:
                    if t.completed_at and t.called_at:
                        diff = (t.completed_at - t.called_at).total_seconds()
                        if diff >= 0:
                            consult_seconds.append(diff)

                avg_consult = (
                    Decimal(f"{sum(consult_seconds) / len(consult_seconds) / 60.0:.2f}")
                    if consult_seconds
                    else None
                )

                # Query existing DailyStats row
                stat_stmt = select(DailyStats).where(
                    DailyStats.clinic_id == clinic.id,
                    DailyStats.doctor_id == doc_id,
                    DailyStats.date == effective_date,
                )
                stat_res = await self.session.execute(stat_stmt)
                existing_stat = stat_res.scalar_one_or_none()

                if existing_stat:
                    existing_stat.seen = seen
                    existing_stat.no_shows = no_shows
                    existing_stat.cancelled = cancelled
                    existing_stat.online_count = online_count
                    existing_stat.walk_in_count = walk_in_count
                    existing_stat.avg_wait_minutes = avg_wait
                    existing_stat.avg_consult_minutes = avg_consult
                else:
                    new_stat = DailyStats(
                        id=uuid.uuid4(),
                        clinic_id=clinic.id,
                        doctor_id=doc_id,
                        date=effective_date,
                        seen=seen,
                        no_shows=no_shows,
                        cancelled=cancelled,
                        online_count=online_count,
                        walk_in_count=walk_in_count,
                        avg_wait_minutes=avg_wait,
                        avg_consult_minutes=avg_consult,
                    )
                    self.session.add(new_stat)

                clinic_stats.append(
                    DoctorStatsSummary(
                        doctor_id=doc_id,
                        seen=seen,
                        no_shows=no_shows,
                        cancelled=cancelled,
                        online_count=online_count,
                        walk_in_count=walk_in_count,
                        avg_wait_minutes=avg_wait,
                        avg_consult_minutes=avg_consult,
                    )
                )

                # Broadcast queue refresh
                try:
                    realtime_client = SupabaseRealtimeClient()
                    await realtime_client.broadcast_queue_update(
                        clinic_id=clinic.id,
                        doctor_id=doc_id,
                        event="token.day_close",
                        token_number=None,
                        total_waiting=0,
                        non_blocking=True,
                    )
                except Exception as exc:
                    logger.debug("Realtime broadcast ignored on day close: %s", exc)

            results.append(
                ClinicDayCloseResult(
                    clinic_id=clinic.id,
                    clinic_name=clinic.name,
                    date=effective_date,
                    tokens_no_show=tokens_no_show,
                    tokens_done=tokens_done,
                    doctor_stats=clinic_stats,
                )
            )

        await self.session.commit()

        return DayCloseResponse(
            success=True,
            processed_count=len(results),
            results=results,
        )

    async def run_daily_brief(
        self,
        clinic_id: uuid.UUID | None = None,
        target_date: date | None = None,
    ) -> DailyBriefJobResponse:
        """Execute automated or on-demand Daily Brief (W-010)."""
        from app.services.ai_service import AIService

        effective_date = target_date or date.today()
        if clinic_id:
            stmt = select(Clinic).where(Clinic.id == clinic_id)
            res = await self.session.execute(stmt)
            clinic = res.scalar_one_or_none()
            if not clinic:
                raise not_found(code="CLINIC_NOT_FOUND", detail=f"Clinic {clinic_id} not found.")
            clinics = [clinic]
        else:
            stmt = select(Clinic).where(Clinic.status.in_(["active", "trial"]))
            res = await self.session.execute(stmt)
            clinics = list(res.scalars().all())

        ai_service = AIService(self.session)
        briefs_count = 0
        errors: list[str] = []

        for clinic in clinics:
            try:
                await ai_service.generate_daily_brief(
                    clinic_id=clinic.id,
                    target_date=effective_date,
                    requested_by=None,
                )
                briefs_count += 1
            except Exception as exc:
                logger.error("Failed to generate daily brief for clinic %s: %s", clinic.id, exc)
                errors.append(f"Clinic {clinic.name} ({clinic.id}): {exc!s}")

        await self.session.commit()
        return DailyBriefJobResponse(
            success=True,
            date=effective_date,
            clinics_processed=len(clinics),
            briefs_generated=briefs_count,
            errors=errors,
        )
