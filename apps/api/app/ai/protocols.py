import uuid
from datetime import date
from typing import Any, Protocol


class AIDataServiceProtocol(Protocol):
    """Protocol for domain services providing data access to the AI layer without direct DB access."""

    async def get_token_status_by_code(self, public_code: str) -> dict[str, Any]: ...

    async def get_clinic_info(self, clinic_id: uuid.UUID) -> dict[str, Any]: ...

    async def get_patient_history(
        self, patient_id: uuid.UUID, clinic_id: uuid.UUID
    ) -> dict[str, Any]: ...

    async def is_ai_notes_enabled(self, clinic_id: uuid.UUID) -> bool: ...

    async def get_daily_stats(
        self, clinic_id: uuid.UUID, start_date: date, end_date: date
    ) -> dict[str, Any]: ...

    async def detect_anomalies(
        self, clinic_id: uuid.UUID, target_date: date
    ) -> list[dict[str, Any]]: ...

    async def get_consult_durations(self, doctor_id: uuid.UUID, limit: int) -> list[int]: ...

    async def save_wait_prediction(
        self,
        token_id: uuid.UUID,
        clinic_id: uuid.UUID,
        predicted_minutes: int,
        model_version: str,
    ) -> dict[str, Any]: ...

    async def check_spend_cap_allowed(self, clinic_id: uuid.UUID | None) -> bool: ...

    async def log_ai_run(self, run_data: dict[str, Any]) -> None: ...
