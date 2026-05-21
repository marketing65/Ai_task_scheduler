"""
Employee matching service.
Fuzzy-matches extracted names against two separate lists:
  - requesters.json  (managers / seniors who assign tasks)
  - doers.json       (employees who perform tasks, with department)

Uses difflib.SequenceMatcher (built-in, no extra dependencies).
Match threshold: 70%
"""

import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Data file paths ───────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "data"
REQUESTERS_FILE = DATA_DIR / "requesters.json"
DOERS_FILE = DATA_DIR / "doers.json"

MATCH_THRESHOLD = 0.70  # 70% minimum similarity

# ── Honorifics to strip before matching ───────────────────────────

_HONORIFICS = re.compile(
    r"\b(sir|ma'?am|madam|mam|ji|bhai|bhaiya|didi|sahab|saheb|"
    r"shri|shrimati|smt\.?|mrs\.?|mr\.?|ms\.?|dr\.?)\b",
    re.IGNORECASE,
)


# ── Internal helpers ──────────────────────────────────────────────


def _normalize(name: str) -> str:
    """Lowercase, strip honorifics, collapse whitespace."""
    name = _HONORIFICS.sub("", name)
    name = re.sub(r"\s+", " ", name).strip().lower()
    
    # Standardize common department/team terms and acronyms
    name = name.replace("management information system", "mis")
    name = name.replace("information technology", "it")
    name = name.replace("human resources", "hr")
    name = name.replace("human resource", "hr")
    name = name.replace("quality assurance", "qa")
    
    return name


def _score(a: str, b: str) -> float:
    """Fuzzy similarity ratio between two normalized strings."""
    return SequenceMatcher(None, a, b).ratio()


def _load_json(path: Path) -> list:
    """Load a JSON file; return empty list if missing."""
    if not path.exists():
        logger.warning(f"Employee data file not found: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: list) -> None:
    """Save data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Public read functions ─────────────────────────────────────────


def load_requesters() -> list[dict]:
    """Return the full requesters list."""
    return _load_json(REQUESTERS_FILE)


def load_doers() -> list[dict]:
    """Return the full doers list."""
    return _load_json(DOERS_FILE)


# ── Matching ──────────────────────────────────────────────────────


def _clean_alphanumeric(text: str) -> str:
    """Remove all non-alphanumeric characters and spaces for deep substring check."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def match_requester(extracted_name: Optional[str]) -> Optional[str]:
    """
    Match an extracted requester name against the requesters list.

    Returns the canonical name if score >= MATCH_THRESHOLD, else None.
    """
    if not extracted_name:
        return None

    query = _normalize(extracted_name)
    query_clean = _clean_alphanumeric(query)
    
    if not query_clean:
        return None

    requesters = load_requesters()

    best_name: Optional[str] = None
    best_score: float = 0.0

    for entry in requesters:
        candidate = _normalize(entry["name"])
        candidate_clean = _clean_alphanumeric(candidate)

        # Layer 1: exact match
        if query == candidate or query_clean == candidate_clean:
            logger.info(f"Requester exact match: '{extracted_name}' → '{entry['name']}'")
            return entry["name"]

        score = 0.0
        # Layer 2: substring match (query inside candidate or vice versa)
        if query_clean in candidate_clean or candidate_clean in query_clean:
            score = 0.90 + (0.09 * _score(query, candidate))
        else:
            # Layer 3: first-name token match
            candidate_tokens = candidate.split()
            if candidate_tokens and query == candidate_tokens[0]:
                score = 0.85
            else:
                # Layer 4: fuzzy ratio
                score = _score(query, candidate)

        if score > best_score:
            best_score = score
            best_name = entry["name"]

    if best_score >= MATCH_THRESHOLD:
        logger.info(
            f"Requester fuzzy match: '{extracted_name}' → '{best_name}' "
            f"(score={best_score:.2f})"
        )
        return best_name

    logger.debug(
        f"No requester match for '{extracted_name}' "
        f"(best score={best_score:.2f} < {MATCH_THRESHOLD})"
    )
    return None


def match_doer(extracted_name: Optional[str]) -> Optional[dict]:
    """
    Match an extracted doer name against the doers list.

    Returns dict {"name": ..., "department": ...} if score >= MATCH_THRESHOLD,
    else None.
    """
    if not extracted_name:
        return None

    query = _normalize(extracted_name)
    query_clean = _clean_alphanumeric(query)

    if not query_clean:
        return None

    doers = load_doers()

    best_entry: Optional[dict] = None
    best_score: float = 0.0

    for entry in doers:
        candidate = _normalize(entry["name"])
        candidate_clean = _clean_alphanumeric(candidate)

        # Layer 1: exact match
        if query == candidate or query_clean == candidate_clean:
            logger.info(f"Doer exact match: '{extracted_name}' → '{entry['name']}'")
            return entry

        score = 0.0
        # Layer 2: substring match (query inside candidate or vice versa)
        if query_clean in candidate_clean or candidate_clean in query_clean:
            score = 0.90 + (0.09 * _score(query, candidate))
        else:
            # Layer 3: first-name token match
            candidate_tokens = candidate.split()
            if candidate_tokens and query == candidate_tokens[0]:
                score = 0.85
            else:
                # Layer 4: fuzzy ratio
                score = _score(query, candidate)

        if score > best_score:
            best_score = score
            best_entry = entry

    if best_score >= MATCH_THRESHOLD:
        logger.info(
            f"Doer fuzzy match: '{extracted_name}' → '{best_entry['name']}' "
            f"(score={best_score:.2f})"
        )
        return best_entry

    logger.debug(
        f"No doer match for '{extracted_name}' "
        f"(best score={best_score:.2f} < {MATCH_THRESHOLD})"
    )
    return None


# ── CRUD operations ───────────────────────────────────────────────


def add_requester(name: str) -> dict:
    """Add a requester. Raises ValueError if already exists."""
    data = load_requesters()
    norm_new = _normalize(name)
    for entry in data:
        if _normalize(entry["name"]) == norm_new:
            raise ValueError(f"Requester '{name}' already exists.")
    new_entry = {"name": name.strip().title()}
    data.append(new_entry)
    _save_json(REQUESTERS_FILE, data)
    return new_entry


def update_requester(old_name: str, new_name: str) -> dict:
    """Rename a requester. Raises ValueError if not found."""
    data = load_requesters()
    norm_old = _normalize(old_name)
    for entry in data:
        if _normalize(entry["name"]) == norm_old:
            entry["name"] = new_name.strip().title()
            _save_json(REQUESTERS_FILE, data)
            return entry
    raise ValueError(f"Requester '{old_name}' not found.")


def delete_requester(name: str) -> bool:
    """Delete a requester. Returns True if deleted, False if not found."""
    data = load_requesters()
    norm = _normalize(name)
    new_data = [e for e in data if _normalize(e["name"]) != norm]
    if len(new_data) == len(data):
        return False
    _save_json(REQUESTERS_FILE, new_data)
    return True


def add_doer(name: str) -> dict:
    """Add a doer. Raises ValueError if already exists."""
    data = load_doers()
    norm_new = _normalize(name)
    for entry in data:
        if _normalize(entry["name"]) == norm_new:
            raise ValueError(f"Doer '{name}' already exists.")
    new_entry = {"name": name.strip()}
    data.append(new_entry)
    _save_json(DOERS_FILE, data)
    return new_entry


def update_doer(old_name: str, new_name: str) -> dict:
    """Update a doer's name. Raises ValueError if not found."""
    data = load_doers()
    norm_old = _normalize(old_name)
    for entry in data:
        if _normalize(entry["name"]) == norm_old:
            entry["name"] = new_name.strip()
            _save_json(DOERS_FILE, data)
            return entry
    raise ValueError(f"Doer '{old_name}' not found.")


def delete_doer(name: str) -> bool:
    """Delete a doer. Returns True if deleted, False if not found."""
    data = load_doers()
    norm = _normalize(name)
    new_data = [e for e in data if _normalize(e["name"]) != norm]
    if len(new_data) == len(data):
        return False
    _save_json(DOERS_FILE, new_data)
    return True
