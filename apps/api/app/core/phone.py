import re

from app.core.errors import unprocessable_entity


def normalize_phone(raw_phone: str, default_country: str = "+92") -> str:
    """Normalize local phone number to E.164 international format.

    Rules:
    - Default country prefix: +92 (Pakistan)
    - 03001234567 -> +923001234567
    - 3001234567 -> +923001234567
    - +92 300 1234567 -> +923001234567
    - Rejects invalid formats with 422 UNPROCESSABLE_ENTITY.
    """
    if not raw_phone:
        raise unprocessable_entity(code="INVALID_PHONE", detail="Phone number is required")

    cleaned = re.sub(r"[\s\-\(\)\.]", "", raw_phone.strip())

    if cleaned.startswith("+"):
        digits = cleaned[1:]
        if not digits.isdigit() or len(digits) < 9 or len(digits) > 15:
            raise unprocessable_entity(
                code="INVALID_PHONE",
                detail="Invalid E.164 phone number format (must contain 9-15 digits)",
            )
        return cleaned

    country_digits = default_country.lstrip("+")

    # 11 digits with leading 0 (e.g. 03001234567)
    if cleaned.startswith("0") and len(cleaned) == 11 and cleaned.isdigit():
        return f"+{country_digits}{cleaned[1:]}"

    # 10 digits without leading 0 (e.g. 3001234567)
    if len(cleaned) == 10 and cleaned.isdigit():
        return f"+{country_digits}{cleaned}"

    # Already has country code digits without plus (e.g. 923001234567)
    if cleaned.startswith(country_digits) and 10 <= len(cleaned) <= 15 and cleaned.isdigit():
        return f"+{cleaned}"

    raise unprocessable_entity(
        code="INVALID_PHONE",
        detail=f"Cannot normalize phone number '{raw_phone}' to E.164 format",
    )
