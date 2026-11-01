import re
import uuid
from decimal import Decimal
from typing import Any

URL_REGEX = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
PHONE_REGEX = re.compile(r"(\+?92[-\s]?|0)?3\d{2}[-\s]?\d{7}", re.IGNORECASE)

DEFAULT_CLINIC_MONTHLY_SPEND_CAP_USD = Decimal("2.00")  # PRD §36.18
DEFAULT_GLOBAL_MONTHLY_SPEND_CAP_USD = Decimal("50.00")
DEFAULT_TOKEN_DAILY_RUN_CAP = 20  # PRD §36.10


class KillSwitchManager:
    """Dynamic runtime kill switch allowing instant suspension of AI features without redeployment."""

    def __init__(self) -> None:
        self.global_killed: bool = False
        self.global_kill_reason: str = "AI service temporarily disabled by administrator."
        self.feature_kill_switches: dict[str, str] = {}
        self.clinic_kill_switches: dict[uuid.UUID, str] = {}

    def activate_global(
        self, reason: str = "Emergency AI service kill switch activated."
    ) -> None:
        self.global_killed = True
        self.global_kill_reason = reason

    def deactivate_global(self) -> None:
        self.global_killed = False

    def disable_feature(
        self, feature: str, reason: str = "Feature temporarily unavailable."
    ) -> None:
        self.feature_kill_switches[feature] = reason

    def enable_feature(self, feature: str) -> None:
        self.feature_kill_switches.pop(feature, None)

    def disable_clinic(
        self, clinic_id: uuid.UUID, reason: str = "AI features disabled for clinic."
    ) -> None:
        self.clinic_kill_switches[clinic_id] = reason

    def enable_clinic(self, clinic_id: uuid.UUID) -> None:
        self.clinic_kill_switches.pop(clinic_id, None)

    def check_is_operational(
        self,
        feature: str | None = None,
        clinic_id: uuid.UUID | None = None,
    ) -> tuple[bool, str | None]:
        if self.global_killed:
            return False, f"AI_SERVICE_DISABLED: {self.global_kill_reason}"

        if feature and feature in self.feature_kill_switches:
            return False, f"AI_FEATURE_DISABLED: {self.feature_kill_switches[feature]}"

        if clinic_id and clinic_id in self.clinic_kill_switches:
            return False, f"AI_CLINIC_DISABLED: {self.clinic_kill_switches[clinic_id]}"

        return True, None


class SpendCapManager:
    """Enforces monthly AI spend caps per clinic and globally (PRD §36.18)."""

    def __init__(
        self,
        default_clinic_cap: Decimal = DEFAULT_CLINIC_MONTHLY_SPEND_CAP_USD,
        global_cap: Decimal = DEFAULT_GLOBAL_MONTHLY_SPEND_CAP_USD,
    ) -> None:
        self.default_clinic_cap = default_clinic_cap
        self.global_cap = global_cap
        self.clinic_caps: dict[uuid.UUID, Decimal] = {}

    def set_clinic_cap(self, clinic_id: uuid.UUID, cap_usd: Decimal) -> None:
        self.clinic_caps[clinic_id] = cap_usd

    def check_spend(
        self,
        clinic_id: uuid.UUID | None,
        clinic_month_spend_usd: Decimal,
        global_month_spend_usd: Decimal,
    ) -> tuple[bool, str | None]:
        if global_month_spend_usd >= self.global_cap:
            return (
                False,
                f"AI_SPEND_CAP_REACHED: Global platform AI monthly budget of ${self.global_cap:.2f} reached. AI service is currently unavailable.",
            )

        if clinic_id:
            cap = self.clinic_caps.get(clinic_id, self.default_clinic_cap)
            if clinic_month_spend_usd >= cap:
                return (
                    False,
                    f"AI_SPEND_CAP_REACHED: Monthly AI spend cap of ${cap:.2f} reached for this clinic. AI service is currently unavailable.",
                )

        return True, None


class RunCapTracker:
    """Enforces daily execution limits per patient token and feature (PRD §36.10)."""

    def __init__(self, token_daily_cap: int = DEFAULT_TOKEN_DAILY_RUN_CAP) -> None:
        self.token_daily_cap = token_daily_cap

    def check_run_cap(
        self,
        current_runs_today: int,
        cap: int | None = None,
    ) -> tuple[bool, str | None]:
        max_runs = cap if cap is not None else self.token_daily_cap
        if current_runs_today >= max_runs:
            return (
                False,
                f"AI_RUN_CAP_EXCEEDED: Daily limit of {max_runs} AI interactions reached for today. Barah-e-karam kal dobara rabta karein.",
            )
        return True, None


# Global instances for runtime access without code deploy
kill_switch_manager = KillSwitchManager()
spend_cap_manager = SpendCapManager()
run_cap_tracker = RunCapTracker()

# Keywords indicating medical diagnosis / prescription inquiry
MEDICAL_QUERY_KEYWORDS = [
    "medicine",
    "dawa",
    "dawakhana",
    "goli",
    "tablet",
    "syrup",
    "dosage",
    "cure",
    "treatment",
    "bimari",
    "bimar",
    "fever",
    "bukhar",
    "pain",
    "dard",
    "infection",
    "prescription",
    "doctor advice",
    "nuskha",
]

MEDICAL_ADVICE_REFUSAL_MESSAGE = (
    "Main sirf token aur queue ki maloomat de sakta hoon, tibbi mashwara (medical advice) "
    "nahi de sakta. Barah-e-karam apne doctor ya clinic se direct rabta karein. "
    "(I can only provide queue and token information, not medical advice. Please consult your doctor directly.)"
)


def strip_urls(text: str) -> str:
    """Strip all web URLs from input text."""
    return URL_REGEX.sub("", text).strip()


def sanitize_patient_input(text: str, max_length: int = 300) -> str:
    """Sanitize patient input: strip URLs, normalize spaces, and limit length to max_length."""
    cleaned = strip_urls(text)
    # Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:max_length]


def is_medical_advice_query(text: str) -> bool:
    """Check if the text is asking for medical advice, diagnoses, or prescriptions."""
    lowered = text.lower()
    return any(keyword in lowered for keyword in MEDICAL_QUERY_KEYWORDS)


def mask_pii_for_ai(data: dict[str, Any]) -> dict[str, Any]:
    """Mask phone numbers and personal identifiers before passing data to AI models or logging."""
    sanitized: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Mask phone numbers
            masked_val = PHONE_REGEX.sub("[PHONE_MASKED]", value)
            if key.lower() in ("phone", "patient_phone", "mobile", "contact"):
                sanitized[key] = "[PHONE_MASKED]"
            elif key.lower() in ("patient_name", "patient_full_name") and " " in masked_val:
                # Keep first name only in patient chat contexts
                sanitized[key] = masked_val.split()[0]
            else:
                sanitized[key] = masked_val
        elif isinstance(value, dict):
            sanitized[key] = mask_pii_for_ai(value)
        elif isinstance(value, list):
            sanitized[key] = [
                mask_pii_for_ai(item) if isinstance(item, dict) else item for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized
