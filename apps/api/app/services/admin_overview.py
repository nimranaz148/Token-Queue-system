import datetime as dt
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tenancy import async_tenant_scope
from app.models.ai import AIRun
from app.models.clinic import Clinic
from app.models.token import Token
from app.schemas.admin_overview import (
    ClinicOverviewItem,
    PlatformKPIs,
    PlatformOverviewResponse,
)


class AdminOverviewService:
    """Service providing platform-level metrics across all clinics for D-002."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_overview(self) -> PlatformOverviewResponse:
        """Fetch Platform Overview KPIs and per-clinic activity metrics."""
        today = dt.date.today()
        seven_days_ago = today - dt.timedelta(days=6)
        three_days_ago = today - dt.timedelta(days=3)
        now_utc = dt.datetime.now(dt.UTC)
        first_of_month = now_utc.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        async with async_tenant_scope(None, bypass=True):
            # 1. Fetch clinics
            clinics_stmt = select(Clinic).order_by(Clinic.created_at.desc())
            clinics_res = await self.session.execute(clinics_stmt)
            clinics = list(clinics_res.scalars().all())

            # 2. Fetch tokens in the last 7 days
            tok_stmt = select(Token).where(Token.visit_date >= seven_days_ago)
            tok_res = await self.session.execute(tok_stmt)
            tokens = list(tok_res.scalars().all())

            # 3. Fetch AI runs this calendar month
            ai_stmt = select(AIRun).where(AIRun.at >= first_of_month)
            ai_res = await self.session.execute(ai_stmt)
            ai_runs = list(ai_res.scalars().all())

        # Process KPIs
        active_clinics = sum(1 for c in clinics if c.status == "active")
        total_clinics = len(clinics)
        tokens_today = sum(1 for t in tokens if t.visit_date == today)
        tokens_7_days = len(tokens)
        ai_spend = sum((r.cost_usd for r in ai_runs), Decimal("0.000000"))
        ai_spend_rounded = Decimal(f"{ai_spend:.2f}")

        # Map tokens per clinic
        clinic_tokens_today: dict[object, int] = {}
        clinic_tokens_7d: dict[object, int] = {}
        clinic_tokens_3d: dict[object, int] = {}
        clinic_last_activity: dict[object, dt.datetime] = {}

        for t in tokens:
            cid = t.clinic_id
            clinic_tokens_7d[cid] = clinic_tokens_7d.get(cid, 0) + 1
            if t.visit_date == today:
                clinic_tokens_today[cid] = clinic_tokens_today.get(cid, 0) + 1
            if t.visit_date >= three_days_ago:
                clinic_tokens_3d[cid] = clinic_tokens_3d.get(cid, 0) + 1

            if t.created_at:
                curr_last = clinic_last_activity.get(cid)
                if not curr_last or t.created_at > curr_last:
                    clinic_last_activity[cid] = t.created_at

        idle_clinics_count = 0
        clinic_rows: list[ClinicOverviewItem] = []

        for c in clinics:
            t_7d = clinic_tokens_7d.get(c.id, 0)
            t_today = clinic_tokens_today.get(c.id, 0)
            t_3d = clinic_tokens_3d.get(c.id, 0)
            last_act = clinic_last_activity.get(c.id) or c.updated_at or c.created_at

            # If zero tokens in the last 3 days, count as idle
            if t_3d == 0:
                idle_clinics_count += 1

            clinic_rows.append(
                ClinicOverviewItem(
                    id=c.id,
                    name=c.name,
                    slug=c.slug,
                    status=c.status,
                    tokens_7d=t_7d,
                    tokens_today=t_today,
                    last_activity=last_act,
                )
            )

        kpis = PlatformKPIs(
            active_clinics=active_clinics,
            total_clinics=total_clinics,
            tokens_today=tokens_today,
            tokens_7_days=tokens_7_days,
            idle_clinics=idle_clinics_count,
            ai_spend_this_month=ai_spend_rounded,
        )

        return PlatformOverviewResponse(kpis=kpis, clinics=clinic_rows)
