"""
Date handling and normalization utilities.
Validates and fixes date formats from GPT output.
"""

import re
from datetime import datetime, timedelta
from dateutil import parser as dateutil_parser
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Hindi relative date mappings ──────────────────────────────────

HINDI_RELATIVE_DATES = {
    "aaj": 0,
    "aaj hi": 0,
    "kal": 1,
    "kal tak": 1,
    "parso": 2,
    "parson": 2,
    "narso": 3,
    "tarso": 4,
}

HINDI_WEEK_OFFSETS = {
    "agle hafte": 7,
    "agale hafte": 7,
    "next week": 7,
    "is hafte": 0,
    "is hafte ke andar": 7,
}


def validate_date_format(date_str: str | None) -> str | None:
    """
    Validate and normalize a date string to YYYY-MM-DD format.

    The GPT model usually returns correct YYYY-MM-DD, but this function
    serves as a safety net to catch and fix edge cases.

    Args:
        date_str: Date string from GPT output, or None.

    Returns:
        Normalized YYYY-MM-DD string, or None if invalid/empty.
    """
    if not date_str or date_str.strip().lower() in ("null", "none", "n/a", ""):
        return None

    date_str = date_str.strip()

    # Already in correct format?
    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            pass

    # Try common formats
    formats_to_try = [
        "%d/%m/%Y",   # 25/04/2026
        "%d-%m-%Y",   # 25-04-2026
        "%m/%d/%Y",   # 04/25/2026
        "%d %B %Y",   # 25 April 2026
        "%d %b %Y",   # 25 Apr 2026
        "%B %d, %Y",  # April 25, 2026
        "%b %d, %Y",  # Apr 25, 2026
        "%d %B",      # 25 April (assume current year)
        "%d %b",      # 25 Apr (assume current year)
        "%B %d",      # April 25 (assume current year)
    ]

    for fmt in formats_to_try:
        try:
            parsed = datetime.strptime(date_str, fmt)
            # If year is 1900 (default), use current year
            if parsed.year == 1900:
                parsed = parsed.replace(year=datetime.now().year)
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Fallback: use dateutil for fuzzy parsing
    try:
        parsed = dateutil_parser.parse(date_str, fuzzy=True)
        return parsed.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass

    logger.warning(f"Could not parse date: '{date_str}'")
    return None


def resolve_hindi_relative_date(text: str) -> str | None:
    """
    Resolve Hindi relative date expressions to YYYY-MM-DD.

    This is used as a fallback if GPT doesn't resolve the date.

    Args:
        text: Hindi/Hinglish text possibly containing a relative date.

    Returns:
        YYYY-MM-DD string if a relative date is found, else None.
    """
    text_lower = text.lower().strip()
    today = datetime.now()

    # Check direct relative mappings
    for phrase, days_offset in HINDI_RELATIVE_DATES.items():
        if phrase in text_lower:
            target = today + timedelta(days=days_offset)
            return target.strftime("%Y-%m-%d")

    # Check week-based offsets
    for phrase, days_offset in HINDI_WEEK_OFFSETS.items():
        if phrase in text_lower:
            target = today + timedelta(days=days_offset)
            return target.strftime("%Y-%m-%d")

    # "agle mahine" / "next month" → 1st of next month
    if "agle mahine" in text_lower or "agale mahine" in text_lower:
        if today.month == 12:
            return datetime(today.year + 1, 1, 1).strftime("%Y-%m-%d")
        return datetime(today.year, today.month + 1, 1).strftime("%Y-%m-%d")

    return None
