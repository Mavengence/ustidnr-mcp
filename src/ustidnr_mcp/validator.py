"""Format validation logic for EU VAT IDs."""

from __future__ import annotations

import re

from ustidnr_mcp.config import settings
from ustidnr_mcp.models import EU_COUNTRY_NAMES, EU_VAT_FORMATS


def sanitize_input(value: str, max_length: int | None = None) -> str:
    """Strip control characters and enforce length limits.

    Args:
        value: Raw input string.
        max_length: Maximum allowed length (defaults to settings.max_input_length).

    Returns:
        Sanitized string with control characters removed.
    """
    limit = max_length if max_length is not None else settings.max_input_length
    # Remove ASCII control characters (0x00-0x1F, 0x7F) except common whitespace
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value)
    return cleaned[:limit]


def extract_country_code(vat_id: str) -> str:
    """Extract the 2-letter country prefix from a VAT ID.

    Returns empty string if no valid prefix found.
    """
    cleaned = vat_id.strip().upper()
    if len(cleaned) < 3:
        return ""
    prefix = cleaned[:2]
    if prefix in EU_VAT_FORMATS:
        return prefix
    return ""


def normalize_vat_id(vat_id: str) -> str:
    """Normalize a VAT ID: uppercase, strip whitespace and common separators."""
    sanitized = sanitize_input(vat_id, max_length=settings.max_vat_id_length)
    return re.sub(r"[\s.\-/]", "", sanitized.strip().upper())


def validate_format(vat_id: str) -> tuple[bool, str, str]:
    """Validate VAT ID format against EU country patterns.

    Returns:
        Tuple of (is_valid, country_code, error_message).
    """
    normalized = normalize_vat_id(vat_id)

    if not normalized:
        return False, "", "VAT ID is empty."

    country_code = extract_country_code(normalized)
    if not country_code:
        return False, "", f"Unknown country prefix: {normalized[:2]}"

    pattern = EU_VAT_FORMATS[country_code]
    if not re.match(pattern, normalized, re.ASCII):
        country_name = EU_COUNTRY_NAMES.get(country_code, country_code)
        return (
            False,
            country_code,
            f"Invalid format for {country_name} ({country_code}). Expected pattern: {pattern}",
        )

    return True, country_code, ""


def validate_german_check_digit(vat_id: str) -> bool:
    """Validate the check digit of a German USt-IdNr (DE + 9 digits).

    Uses the ISO/IEC 7064 MOD 11,10 algorithm as specified by the BZSt.
    """
    normalized = normalize_vat_id(vat_id)
    if not re.match(r"^DE\d{9}$", normalized):
        return False

    digits = normalized[2:]
    product = 10

    for i in range(8):
        total = (int(digits[i]) + product) % 10
        if total == 0:
            total = 10
        product = (2 * total) % 11

    check_digit = 11 - product
    if check_digit == 10:
        check_digit = 0

    return check_digit == int(digits[8])
