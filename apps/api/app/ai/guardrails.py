import re
from typing import Any

URL_REGEX = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
PHONE_REGEX = re.compile(r"(\+?92[-\s]?|0)?3\d{2}[-\s]?\d{7}", re.IGNORECASE)

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
