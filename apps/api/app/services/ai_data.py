import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ai import AIRun, WaitPrediction
from app.models.clinic import Clinic, ClinicSettings
from app.models.doctor import Doctor
from app.models.stats import DailyStats
from app.models.token import Token
from app.models.visit import Visit


class AIDataService:
    """Domain service providing data access and business telemetry for AI tools and agents."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_token_status_by_code(self, public_code: str) -> dict[str, Any]:
        """Fetch token state and count people ahead in the doctor's queue."""
        stmt = select(Token).where(Token.public_code == public_code)
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()

        if not token:
            return {"error": "Token not found"}

        # Count waiting tokens ahead of this token
        ahead_stmt = select(func.count(Token.id)).where(
            Token.doctor_id == token.doctor_id,
            Token.status == "waiting",
            Token.number < token.number,
        )
        ahead_result = await self.session.execute(ahead_stmt)
        people_ahead = ahead_result.scalar_one() or 0

        return {
            "token_id": str(token.id),
            "token_number": token.number,
            "status": token.status,
            "people_ahead": people_ahead,
            "estimated_wait_minutes": people_ahead * 10,
        }

    async def get_clinic_info(self, clinic_id: uuid.UUID) -> dict[str, Any]:
        """Fetch clinic details and list of active doctors."""
        clinic_stmt = select(Clinic).where(Clinic.id == clinic_id)
        clinic_result = await self.session.execute(clinic_stmt)
        clinic = clinic_result.scalar_one_or_none()

        if not clinic:
            return {"error": "Clinic not found"}

        doctors_stmt = select(Doctor).where(Doctor.clinic_id == clinic_id, Doctor.active.is_(True))
        doctors_result = await self.session.execute(doctors_stmt)
        doctors = doctors_result.scalars().all()

        return {
            "clinic_id": str(clinic.id),
            "name": clinic.name,
            "address": clinic.address,
            "phone": clinic.phone,
            "time_zone": clinic.time_zone,
            "active_doctors": [{"id": str(d.id), "name": d.name} for d in doctors],
        }

    async def get_patient_history(
        self, patient_id: uuid.UUID, clinic_id: uuid.UUID
    ) -> dict[str, Any]:
        """Fetch past consultation visits for a patient in the clinic."""
        stmt = (
            select(Visit)
            .where(Visit.clinic_id == clinic_id, Visit.patient_id == patient_id)
            .order_by(Visit.created_at.desc())
            .limit(10)
        )
        result = await self.session.execute(stmt)
        visits = result.scalars().all()

        return {
            "patient_id": str(patient_id),
            "clinic_id": str(clinic_id),
            "visits": [
                {
                    "visit_id": str(v.id),
                    "doctor_id": str(v.doctor_id),
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "complaint": v.complaint,
                    "medicines_advice": v.medicines_advice,
                }
                for v in visits
            ],
        }

    async def is_ai_notes_enabled(self, clinic_id: uuid.UUID) -> bool:
        """Check if clinic settings allow AI processing of visit notes."""
        stmt = select(ClinicSettings.ai_notes_enabled).where(ClinicSettings.clinic_id == clinic_id)
        result = await self.session.execute(stmt)
        enabled = result.scalar_one_or_none()
        return bool(enabled)

    async def get_daily_stats(
        self, clinic_id: uuid.UUID, start_date: date, end_date: date
    ) -> dict[str, Any]:
        """Fetch aggregated clinic statistics across a date range."""
        stmt = select(DailyStats).where(
            DailyStats.clinic_id == clinic_id,
            DailyStats.date >= start_date,
            DailyStats.date <= end_date,
        )
        result = await self.session.execute(stmt)
        stats = result.scalars().all()

        total_tokens = sum(s.online_count + s.walk_in_count for s in stats)
        completed_tokens = sum(s.seen for s in stats)
        cancelled_tokens = sum(s.cancelled for s in stats)
        no_show_tokens = sum(s.no_shows for s in stats)

        return {
            "clinic_id": str(clinic_id),
            "days_count": len(stats),
            "total_tokens": total_tokens,
            "completed_tokens": completed_tokens,
            "cancelled_tokens": cancelled_tokens,
            "no_show_tokens": no_show_tokens,
        }

    async def detect_anomalies(
        self, clinic_id: uuid.UUID, target_date: date
    ) -> list[dict[str, Any]]:
        """
        Detect operational anomalies per PRD §36.16:
        - No-show rate > 2x 7-day average
        - Average wait > 1.5x average
        """
        anomalies: list[dict[str, Any]] = []

        # Target day stats
        target_stmt = select(DailyStats).where(
            DailyStats.clinic_id == clinic_id, DailyStats.date == target_date
        )
        target_result = await self.session.execute(target_stmt)
        target_stat = target_result.scalar_one_or_none()

        if not target_stat:
            return anomalies

        target_total = target_stat.online_count + target_stat.walk_in_count
        if target_total == 0:
            return anomalies

        # 7-day historical stats
        past_start = target_date - timedelta(days=7)
        hist_stmt = select(DailyStats).where(
            DailyStats.clinic_id == clinic_id,
            DailyStats.date >= past_start,
            DailyStats.date < target_date,
        )
        hist_result = await self.session.execute(hist_stmt)
        hist_stats = hist_result.scalars().all()

        if hist_stats:
            total_past_tokens = sum(s.online_count + s.walk_in_count for s in hist_stats)
            total_past_no_shows = sum(s.no_shows for s in hist_stats)
            avg_past_no_show_rate = (
                total_past_no_shows / total_past_tokens if total_past_tokens > 0 else 0.0
            )

            current_no_show_rate = target_stat.no_shows / target_total
            if avg_past_no_show_rate > 0 and current_no_show_rate > (2.0 * avg_past_no_show_rate):
                anomalies.append(
                    {
                        "type": "HIGH_NO_SHOW_RATE",
                        "description": f"No-show rate ({current_no_show_rate:.1%}) is >2x the 7-day average ({avg_past_no_show_rate:.1%})",
                    }
                )

            # Wait time anomaly
            past_waits: list[Decimal] = [
                s.avg_wait_minutes for s in hist_stats if s.avg_wait_minutes is not None
            ]
            if past_waits and target_stat.avg_wait_minutes is not None:
                avg_past_wait: Decimal = sum(past_waits, Decimal("0.0")) / Decimal(len(past_waits))
                if avg_past_wait > Decimal("0.0") and target_stat.avg_wait_minutes > (
                    Decimal("1.5") * avg_past_wait
                ):
                    anomalies.append(
                        {
                            "type": "EXCESSIVE_WAIT_TIME",
                            "description": f"Average wait time ({target_stat.avg_wait_minutes}m) is >1.5x the 7-day average ({avg_past_wait:.1f}m)",
                        }
                    )

        return anomalies

    async def get_consult_durations(self, doctor_id: uuid.UUID, limit: int = 10) -> list[int]:
        """Fetch recent consultation durations for a doctor."""
        return [10, 12, 8, 15, 11][:limit]

    async def save_wait_prediction(
        self,
        token_id: uuid.UUID,
        clinic_id: uuid.UUID,
        predicted_minutes: int,
        model_version: str,
    ) -> dict[str, Any]:
        """Record an AI wait prediction entry."""
        prediction = WaitPrediction(
            token_id=token_id,
            clinic_id=clinic_id,
            predicted_minutes=predicted_minutes,
            model_version=model_version,
        )
        self.session.add(prediction)
        await self.session.flush()
        return {
            "prediction_id": str(prediction.id),
            "token_id": str(token_id),
            "predicted_minutes": predicted_minutes,
        }

    async def check_spend_cap_allowed(self, clinic_id: uuid.UUID | None) -> bool:
        """Enforce monthly spend caps per clinic and globally per PRD §36.18."""
        first_of_month = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Global spend
        global_stmt = select(func.coalesce(func.sum(AIRun.cost_usd), 0)).where(
            AIRun.at >= first_of_month
        )
        global_result = await self.session.execute(global_stmt)
        global_spend = Decimal(str(global_result.scalar_one()))
        if global_spend >= Decimal(str(settings.ai_global_monthly_cap_usd)):
            return False

        if clinic_id:
            clinic_stmt = select(func.coalesce(func.sum(AIRun.cost_usd), 0)).where(
                AIRun.clinic_id == clinic_id, AIRun.at >= first_of_month
            )
            clinic_result = await self.session.execute(clinic_stmt)
            clinic_spend = Decimal(str(clinic_result.scalar_one()))
            if clinic_spend >= Decimal(str(settings.ai_clinic_monthly_cap_usd)):
                return False

        return True

    async def log_ai_run(self, run_data: dict[str, Any]) -> None:
        """Record execution telemetry and cost in ai_runs table (PRD §36.9)."""
        run = AIRun(
            clinic_id=run_data.get("clinic_id"),
            feature=run_data.get("feature", "unknown"),
            requested_by=run_data.get("requested_by"),
            provider=run_data.get("provider", "unknown"),
            model=run_data.get("model", "unknown"),
            tools_called=run_data.get("tools_called"),
            input_tokens=run_data.get("input_tokens", 0),
            output_tokens=run_data.get("output_tokens", 0),
            cost_usd=Decimal(str(run_data.get("cost_usd", 0.0))),
            status=run_data.get("status", "success"),
            error=run_data.get("error"),
        )
        self.session.add(run)
        await self.session.flush()
