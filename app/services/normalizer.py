"""
Name and department normalization utilities.
Strips honorifics, normalizes department names, and standardizes casing.
"""

import re
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Honorifics to strip from names ────────────────────────────────

HONORIFICS = [
    r"\bsir\b",
    r"\bma'?am\b",
    r"\bmadam\b",
    r"\bmam\b",
    r"\bji\b",
    r"\bbhai\b",
    r"\bbhaiya\b",
    r"\bdidi\b",
    r"\bsahab\b",
    r"\bsaheb\b",
    r"\bbabu\b",
    r"\bmahodaya\b",
    r"\bshri\b",
    r"\bshrimati\b",
    r"\bsmt\.?\s*",
    r"\bmrs\.?\s*",
    r"\bmr\.?\s*",
    r"\bms\.?\s*",
    r"\bdr\.?\s*",
]

# ── Department name normalization map ─────────────────────────────

DEPARTMENT_ALIASES = {
    # HR
    "hr": "HR",
    "human resource": "HR",
    "human resources": "HR",
    "hr department": "HR",
    "hr mein": "HR",
    "hr me": "HR",
    # Production
    "production": "Production",
    "production side": "Production",
    "production department": "Production",
    "manufacturing": "Production",
    # Finance
    "finance": "Finance",
    "finance department": "Finance",
    "finance mein": "Finance",
    # Accounts
    "accounts": "Accounts",
    "accounts wale": "Accounts",
    "accounting": "Accounts",
    "accounts department": "Accounts",
    # IT
    "it": "IT",
    "it department": "IT",
    "information technology": "IT",
    "tech": "IT",
    "technical": "IT",
    # Sales
    "sales": "Sales",
    "sales department": "Sales",
    "sales team": "Sales",
    # Marketing
    "marketing": "Marketing",
    "marketing department": "Marketing",
    "marketing team": "Marketing",
    # Operations
    "operations": "Operations",
    "ops": "Operations",
    "operations department": "Operations",
    # Admin
    "admin": "Admin",
    "administration": "Admin",
    "admin department": "Admin",
    # Legal
    "legal": "Legal",
    "legal department": "Legal",
    "legal team": "Legal",
    # Quality
    "quality": "Quality",
    "qa": "Quality",
    "quality assurance": "Quality",
    "quality department": "Quality",
    # Logistics
    "logistics": "Logistics",
    "logistics department": "Logistics",
    "supply chain": "Logistics",
    # R&D
    "r&d": "R&D",
    "research": "R&D",
    "research and development": "R&D",
    # Procurement
    "procurement": "Procurement",
    "purchase": "Procurement",
    "purchasing": "Procurement",
}


def normalize_name(name: str | None) -> str | None:
    """
    Normalize a person's name by stripping honorifics and fixing casing.

    Args:
        name: Raw name string (e.g., "Mukesh sir", "Simran mam").

    Returns:
        Clean name (e.g., "Mukesh", "Simran"), or None if empty.

    Examples:
        >>> normalize_name("Mukesh sir")
        'Mukesh'
        >>> normalize_name("Simran mam")
        'Simran'
        >>> normalize_name("Dr. Sharma ji")
        'Sharma'
    """
    if not name or not name.strip():
        return None

    cleaned = name.strip()

    # Remove honorifics (case-insensitive)
    for pattern in HONORIFICS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Title-case the result
    if cleaned:
        cleaned = cleaned.title()
        return cleaned

    return None


def normalize_department(department: str | None) -> str | None:
    """
    Normalize a department name to its standard form.

    Args:
        department: Raw department string (e.g., "HR mein", "production side").

    Returns:
        Standardized department name (e.g., "HR", "Production"), or None.

    Examples:
        >>> normalize_department("HR mein")
        'HR'
        >>> normalize_department("production side")
        'Production'
        >>> normalize_department("accounts wale")
        'Accounts'
    """
    if not department or not department.strip():
        return None

    cleaned = department.strip().lower()

    # Remove common Hindi suffixes
    suffixes_to_strip = [
        " mein", " me", " mei", " side", " wale", " wala",
        " walon", " ka", " ki", " ke", " department", " dept",
        " team", " section", " division",
    ]
    for suffix in suffixes_to_strip:
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)].strip()

    # Look up in alias map
    if cleaned in DEPARTMENT_ALIASES:
        return DEPARTMENT_ALIASES[cleaned]

    # If not in map, title-case and return as-is
    result = cleaned.title()
    logger.debug(f"Department '{department}' not in alias map, using: {result}")
    return result
