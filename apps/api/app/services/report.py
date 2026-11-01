import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import forbidden, not_found
from app.models.doctor import Doctor
from app.models.stats import DailyStats
from app.models.token import Token
from app.schemas.auth import CurrentUser, Role
from app.schemas.report import (
    DailyReportKPIs,
    DailyReportResponse,
    DailyTrendItem,
)


class ReportService:
    """Service generating Roz ki Report (F-010 / D-001) metrics from daily_stats and tokens."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_daily_report(
        self,
        clinic_id: uuid.UUID,
        target_date: dt.date,
        current_user: CurrentUser,
        doctor_id: uuid.UUID | None = None,
    ) -> DailyReportResponse:
        """Fetch daily KPI metrics and 7-day trend for a clinic (F-010 / D-001).

        Roles:
        - Owner & Platform Admin: can view all doctors or filter by doctor.
        - Doctor: can only view their own performance metrics.
        - Other roles: 403 Forbidden.
        """
        # Role authorization
        if current_user.role == Role.DOCTOR:
            # Enforce doctor can only view own metrics
            if doctor_id and current_user.doctor_id and doctor_id != current_user.doctor_id:
                raise forbidden(code="FORBIDDEN", detail="Doctors can only view their own reports.")
            doctor_id = current_user.doctor_id
        elif current_user.role not in {Role.OWNER, Role.PLATFORM_ADMIN}:
            raise forbidden(code="FORBIDDEN", detail="Role not authorized to view reports.")

        # Resolve doctor name if filtered
        doctor_name: str | None = None
        if doctor_id:
            doc_stmt = select(Doctor.name).where(
                Doctor.clinic_id == clinic_id, Doctor.id == doctor_id
            )
            doc_res = await self.session.execute(doc_stmt)
            doctor_name = doc_res.scalar_one_or_none()
            if not doctor_name:
                raise not_found(
                    code="DOCTOR_NOT_FOUND", detail=f"Doctor {doctor_id} not found in this clinic."
                )

        # 1. Fetch metrics for target_date
        # Check DailyStats first
        stat_stmt = select(DailyStats).where(
            DailyStats.clinic_id == clinic_id,
            DailyStats.date == target_date,
        )
        if doctor_id:
            stat_stmt = stat_stmt.where(DailyStats.doctor_id == doctor_id)

        stat_res = await self.session.execute(stat_stmt)
        stats = list(stat_res.scalars().all())

        if stats:
            patients_seen = sum(s.seen for s in stats)
            no_shows = sum(s.no_shows for s in stats)
            cancelled_count = sum(s.cancelled for s in stats)
            online_count = sum(s.online_count for s in stats)
            walk_in_count = sum(s.walk_in_count for s in stats)
            total_tokens = online_count + walk_in_count

            # Weighted average wait
            waits = [s.avg_wait_minutes for s in stats if s.avg_wait_minutes is not None]
            avg_wait = Decimal(f"{sum(waits) / len(waits):.1f}") if waits else None

            online_share = (
                Decimal(f"{(online_count / total_tokens) * 100:.1f}")
                if total_tokens > 0
                else Decimal("0.0")
            )
        else:
            # Calculate live from Token table for today or unclosed date
            tok_stmt = select(Token).where(
                Token.clinic_id == clinic_id,
                Token.visit_date == target_date,
            )
            if doctor_id:
                tok_stmt = tok_stmt.where(Token.doctor_id == doctor_id)

            tok_res = await self.session.execute(tok_stmt)
            tokens = list(tok_res.scalars().all())

            patients_seen = sum(1 for t in tokens if t.status == "done")
            no_shows = sum(1 for t in tokens if t.status == "no_show")
            cancelled_count = sum(1 for t in tokens if t.status == "cancelled")
            online_count = sum(1 for t in tokens if t.source == "online")
            walk_in_count = sum(1 for t in tokens if t.source == "walk_in")
            total_tokens = online_count + walk_in_count

            wait_diffs: list[float] = []
            for t in tokens:
                if t.called_at and t.arrived_at:
                    diff = (t.called_at - t.arrived_at).total_seconds() / 60.0
                    if diff >= 0:
                        wait_diffs.append(diff)
                elif t.called_at and t.created_at:
                    diff = (t.called_at - t.created_at).total_seconds() / 60.0
                    if diff >= 0:
                        wait_diffs.append(diff)

            avg_wait = Decimal(f"{sum(wait_diffs) / len(wait_diffs):.1f}") if wait_diffs else None

            online_share = (
                Decimal(f"{(online_count / total_tokens) * 100:.1f}")
                if total_tokens > 0
                else Decimal("0.0")
            )

        kpis = DailyReportKPIs(
            patients_seen=patients_seen,
            avg_wait_minutes=avg_wait,
            no_shows=no_shows,
            online_share_pct=online_share,
            total_tokens=total_tokens,
            online_count=online_count,
            walk_in_count=walk_in_count,
            cancelled_count=cancelled_count,
        )

        # 2. Compute 7-day trend ending on target_date
        past_7_dates = [target_date - dt.timedelta(days=i) for i in range(6, -1, -1)]
        start_date = past_7_dates[0]

        trend_stmt = select(DailyStats).where(
            DailyStats.clinic_id == clinic_id,
            DailyStats.date >= start_date,
            DailyStats.date <= target_date,
        )
        if doctor_id:
            trend_stmt = trend_stmt.where(DailyStats.doctor_id == doctor_id)

        trend_res = await self.session.execute(trend_stmt)
        hist_stats = list(trend_res.scalars().all())

        stats_by_date: dict[dt.date, list[DailyStats]] = {}
        for s in hist_stats:
            stats_by_date.setdefault(s.date, []).append(s)

        trend_items: list[DailyTrendItem] = []
        for d in past_7_dates:
            day_stats = stats_by_date.get(d, [])
            if day_stats:
                d_seen = sum(s.seen for s in day_stats)
                d_no_shows = sum(s.no_shows for s in day_stats)
                d_total = sum(s.online_count + s.walk_in_count for s in day_stats)
            elif d == target_date:
                d_seen = patients_seen
                d_no_shows = no_shows
                d_total = total_tokens
            else:
                d_seen = 0
                d_no_shows = 0
                d_total = 0

            trend_items.append(
                DailyTrendItem(
                    date=d,
                    day_name=d.strftime("%a"),
                    patients_seen=d_seen,
                    no_shows=d_no_shows,
                    total_tokens=d_total,
                )
            )

        return DailyReportResponse(
            clinic_id=clinic_id,
            date=target_date,
            doctor_id=doctor_id,
            doctor_name=doctor_name,
            kpis=kpis,
            trend_7_days=trend_items,
        )
