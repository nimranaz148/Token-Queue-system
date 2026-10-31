import hashlib
from typing import Any


def mask_phone(phone: str | None) -> str | None:
    """Mask phone number preserving prefix and suffix (e.g. 0300****567)."""
    if not phone:
        return phone
    p = str(phone).strip()
    if len(p) <= 7:
        return "***"
    return p[:4] + "*" * (len(p) - 7) + p[-3:]


def mask_name(name: str | None) -> str | None:
    """Mask personal name preserving first letter of each word (e.g. M*** A***)."""
    if not name:
        return name
    parts = str(name).strip().split()
    return " ".join(f"{p[0]}***" for p in parts if p)


def mask_email(email: str | None) -> str | None:
    """Mask email username preserving initial and domain (e.g. j***@example.com)."""
    if not email or "@" not in email:
        return email
    user, domain = email.split("@", 1)
    masked_user = f"{user[0]}***" if len(user) > 1 else "***"
    return f"{masked_user}@{domain}"


def hash_ip(ip: str | None) -> str | None:
    """Hash IP address using SHA-256 for privacy-preserving audit forensics."""
    if not ip:
        return None
    return hashlib.sha256(ip.strip().encode("utf-8")).hexdigest()[:16]


_REDACTED_TEXT = "[REDACTED]"
_REDACTED_HEALTH_TEXT = "[REDACTED_HEALTH_DATA]"


def mask_sensitive_data(data: dict[str, Any] | None) -> dict[str, Any] | None:
    """Recursively mask sensitive personal and health fields in data dictionaries."""
    if data is None:
        return None

    masked: dict[str, Any] = {}
    for key, value in data.items():
        k = key.lower()

        if value is None:
            masked[key] = None
        elif isinstance(value, dict):
            masked[key] = mask_sensitive_data(value)
        elif isinstance(value, list):
            masked[key] = [
                mask_sensitive_data(item) if isinstance(item, dict) else item for item in value
            ]
        elif k in {"phone", "mobile", "cell", "phone_number"}:
            masked[key] = mask_phone(str(value))
        elif k in {"name", "patient_name", "full_name"}:
            masked[key] = mask_name(str(value))
        elif k in {"email"}:
            masked[key] = mask_email(str(value))
        elif k in {"password", "secret", "token", "access_token", "refresh_token", "api_key"}:
            masked[key] = _REDACTED_TEXT
        elif k in {"notes", "private_notes", "diagnosis", "chief_complaint"}:
            masked[key] = _REDACTED_HEALTH_TEXT
        elif k in {"cnic"}:
            masked[key] = "[REDACTED_CNIC]"
        else:
            masked[key] = value

    return masked
