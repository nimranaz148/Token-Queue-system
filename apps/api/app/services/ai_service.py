import datetime as dt
import uuid
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.daily_brief import DailyBriefAgent
from app.ai.agents.patient_chat import PatientChatAgent
from app.ai.providers.manager import ProviderManager
from app.ai.types import AgentMessage
from app.core.tenancy import async_tenant_scope
from app.models.ai import AIBrief, AIRun, ChatMessage
from app.models.clinic import Clinic, ClinicSettings
from app.models.token import Token
from app.services.ai_data import AIDataService


class AIService:
    """Service handling AI Activity, Daily Brief, Patient Chat, and Command Center analytics."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.data_service = AIDataService(session)

    async def get_activity_log(
        self,
        caller_clinic_id: uuid.UUID | None,
        is_platform_admin: bool,
        start_date: dt.date | None = None,
        end_date: dt.date | None = None,
        feature: str | None = None,
        filter_clinic_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AIRun], int]:
        """Fetch AI activity telemetry logs with tenant scoping and filtering."""
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        stmt = select(AIRun)
        count_stmt = select(func.count(AIRun.id))

        # Enforce multi-clinic SaaS isolation
        if not is_platform_admin:
            if not caller_clinic_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Clinic context is required for non-admin callers",
                )
            stmt = stmt.where(AIRun.clinic_id == caller_clinic_id)
            count_stmt = count_stmt.where(AIRun.clinic_id == caller_clinic_id)
        else:
            if filter_clinic_id:
                stmt = stmt.where(AIRun.clinic_id == filter_clinic_id)
                count_stmt = count_stmt.where(AIRun.clinic_id == filter_clinic_id)

        if feature:
            stmt = stmt.where(AIRun.feature == feature)
            count_stmt = count_stmt.where(AIRun.feature == feature)

        if start_date:
            start_dt = dt.datetime.combine(start_date, dt.time.min, tzinfo=dt.UTC)
            stmt = stmt.where(AIRun.at >= start_dt)
            count_stmt = count_stmt.where(AIRun.at >= start_dt)

        if end_date:
            end_dt = dt.datetime.combine(end_date, dt.time.max, tzinfo=dt.UTC)
            stmt = stmt.where(AIRun.at <= end_dt)
            count_stmt = count_stmt.where(AIRun.at <= end_dt)

        stmt = stmt.order_by(desc(AIRun.at)).limit(limit).offset(offset)

        total_res = await self.session.execute(count_stmt)
        total = total_res.scalar_one() or 0

        items_res = await self.session.execute(stmt)
        items = list(items_res.scalars().all())

        return items, total

    async def get_command_center_kpis(
        self,
        caller_clinic_id: uuid.UUID | None,
        is_platform_admin: bool,
        filter_clinic_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Aggregate AI Command Center KPIs per PRD §7 D-003 and PRD §29.3."""
        scope_clinic_id = filter_clinic_id if is_platform_admin else caller_clinic_id

        # Total AI calls
        calls_stmt = select(func.count(AIRun.id))
        failures_stmt = select(func.count(AIRun.id)).where(AIRun.status == "error")
        cost_stmt = select(func.coalesce(func.sum(AIRun.cost_usd), Decimal("0.000000")))

        if scope_clinic_id:
            calls_stmt = calls_stmt.where(AIRun.clinic_id == scope_clinic_id)
            failures_stmt = failures_stmt.where(AIRun.clinic_id == scope_clinic_id)
            cost_stmt = cost_stmt.where(AIRun.clinic_id == scope_clinic_id)

        calls_res = await self.session.execute(calls_stmt)
        total_calls = calls_res.scalar_one() or 0

        fail_res = await self.session.execute(failures_stmt)
        failures = fail_res.scalar_one() or 0

        cost_res = await self.session.execute(cost_stmt)
        total_cost = Decimal(str(cost_res.scalar_one() or 0))

        # Fallback rate: ratio of runs that required provider fallback
        # Evaluated from error status or provider fallback indicator in telemetry
        fallback_stmt = select(func.count(AIRun.id)).where(
            AIRun.provider != "openrouter",
            AIRun.status == "success",
        )
        if scope_clinic_id:
            fallback_stmt = fallback_stmt.where(AIRun.clinic_id == scope_clinic_id)
        fallback_res = await self.session.execute(fallback_stmt)
        fallback_count = fallback_res.scalar_one() or 0
        fallback_rate = (fallback_count / total_calls) if total_calls > 0 else 0.0

        # Thumbs-down rate from ai_briefs
        briefs_total_stmt = select(func.count(AIBrief.id)).where(AIBrief.feedback.isnot(None))
        briefs_down_stmt = select(func.count(AIBrief.id)).where(AIBrief.feedback == "down")
        if scope_clinic_id:
            briefs_total_stmt = briefs_total_stmt.where(AIBrief.clinic_id == scope_clinic_id)
            briefs_down_stmt = briefs_down_stmt.where(AIBrief.clinic_id == scope_clinic_id)

        b_total_res = await self.session.execute(briefs_total_stmt)
        b_total = b_total_res.scalar_one() or 0

        b_down_res = await self.session.execute(briefs_down_stmt)
        b_down = b_down_res.scalar_one() or 0

        thumbs_down_rate = (b_down / b_total) if b_total > 0 else 0.0

        # Recent runs (top 10)
        recent_stmt = select(AIRun)
        if scope_clinic_id:
            recent_stmt = recent_stmt.where(AIRun.clinic_id == scope_clinic_id)
        recent_stmt = recent_stmt.order_by(desc(AIRun.at)).limit(10)
        recent_res = await self.session.execute(recent_stmt)
        recent_runs = list(recent_res.scalars().all())

        return {
            "ai_calls": total_calls,
            "failures": failures,
            "fallback_rate": round(fallback_rate, 4),
            "total_cost_usd": total_cost,
            "thumbs_down_rate": round(thumbs_down_rate, 4),
            "recent_runs": recent_runs,
        }

    async def get_daily_brief(self, clinic_id: uuid.UUID, target_date: dt.date) -> AIBrief:
        """Fetch the daily brief for a given clinic and date."""
        stmt = select(AIBrief).where(AIBrief.clinic_id == clinic_id, AIBrief.date == target_date)
        res = await self.session.execute(stmt)
        brief = res.scalar_one_or_none()
        if not brief:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Daily brief for this date not found",
            )
        return brief

    async def generate_daily_brief(
        self, clinic_id: uuid.UUID, target_date: dt.date, requested_by: uuid.UUID | None = None
    ) -> AIBrief:
        """Execute DailyBriefAgent to generate or refresh the nightly brief."""
        agent = DailyBriefAgent(service=self.data_service)
        result = await agent.generate_brief(
            clinic_id=clinic_id,
            target_date=target_date,
            requested_by=requested_by,
        )

        # Upsert or insert AIBrief
        stmt = select(AIBrief).where(AIBrief.clinic_id == clinic_id, AIBrief.date == target_date)
        res = await self.session.execute(stmt)
        brief = res.scalar_one_or_none()

        body_md = result.get("brief_md") or result.get("brief_markdown", "No brief content generated.")
        anomalies = result.get("anomalies", [])

        if brief:
            brief.body_md = body_md
            brief.anomalies = anomalies
        else:
            brief = AIBrief(
                clinic_id=clinic_id,
                date=target_date,
                body_md=body_md,
                anomalies=anomalies,
            )
            self.session.add(brief)

        await self.session.flush()
        return brief

    async def submit_brief_feedback(
        self, clinic_id: uuid.UUID, brief_id: uuid.UUID, feedback: str
    ) -> AIBrief:
        """Record owner feedback ('up' or 'down') for an AI brief."""
        stmt = select(AIBrief).where(AIBrief.clinic_id == clinic_id, AIBrief.id == brief_id)
        res = await self.session.execute(stmt)
        brief = res.scalar_one_or_none()
        if not brief:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AI brief not found",
            )
        brief.feedback = feedback
        await self.session.flush()
        return brief

    async def get_patient_chat_history(
        self, public_code: str
    ) -> tuple[Token, list[ChatMessage]]:
        """Fetch chat history for a patient token by its unguessable public code."""
        stmt = select(Token).where(Token.public_code == public_code)
        res = await self.session.execute(stmt)
        token = res.scalar_one_or_none()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found",
            )

        chat_stmt = (
            select(ChatMessage)
            .where(ChatMessage.token_id == token.id)
            .order_by(ChatMessage.at.asc())
        )
        chat_res = await self.session.execute(chat_stmt)
        messages = list(chat_res.scalars().all())
        return token, messages

    async def send_patient_message(
        self, public_code: str, message: str
    ) -> tuple[str, list[str]]:
        """Execute PatientChatAgent with strict 20 msg/day rate limiting and guardrails."""
        stmt = select(Token).where(Token.public_code == public_code)
        res = await self.session.execute(stmt)
        token = res.scalar_one_or_none()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Token not found",
            )

        # Rate limit: 20 messages per token per day (PRD §5.3 F-019 & PRD §36.10)
        today_start = dt.datetime.combine(dt.date.today(), dt.time.min, tzinfo=dt.UTC)
        count_stmt = select(func.count(ChatMessage.id)).where(
            ChatMessage.token_id == token.id,
            ChatMessage.role == "patient",
            ChatMessage.at >= today_start,
        )
        count_res = await self.session.execute(count_stmt)
        msg_count = count_res.scalar_one() or 0
        if msg_count >= 20:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rozana 20 messages ki had poori ho chuki hai (Daily limit of 20 messages reached).",
            )

        # Load recent chat history for context
        history_stmt = (
            select(ChatMessage)
            .where(ChatMessage.token_id == token.id)
            .order_by(ChatMessage.at.asc())
            .limit(6)
        )
        hist_res = await self.session.execute(history_stmt)
        history_records = list(hist_res.scalars().all())
        agent_history = [
            AgentMessage(role=h.role, content=h.content) for h in history_records
        ]

        # Record patient message
        patient_msg = ChatMessage(
            clinic_id=token.clinic_id,
            token_id=token.id,
            role="patient",
            content=message,
        )
        self.session.add(patient_msg)
        await self.session.flush()

        # Run agent
        agent = PatientChatAgent(service=self.data_service)
        result = await agent.answer(
            public_code=public_code,
            user_message=message,
            conversation_history=agent_history,
        )

        reply_text = result.get("response", "Maaf kijiye, masla pesh aya.")
        tool_calls = [
            tc["tool"] if isinstance(tc, dict) and "tool" in tc else str(tc)
            for tc in result.get("tool_calls", [])
        ]

        # Record assistant reply
        assistant_msg = ChatMessage(
            clinic_id=token.clinic_id,
            token_id=token.id,
            role="assistant",
            content=reply_text,
        )
        self.session.add(assistant_msg)
        await self.session.flush()

        return reply_text, tool_calls
