
import re
from collections.abc import Mapping, Sequence
from datetime import date
from typing import Optional


_DATE_TOKEN = re.compile(r"^(\d{4})(?:[-/](\d{1,2}))?(?:[-/](\d{1,2}))?$")
_MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}
_CURRENT_TOKENS = {"present", "current", "now", "ongoing", "today"}
_STINT_KEYS = {
    "company", "title", "role", "position", "employer", "organization",
    "start", "start_date", "from", "end", "end_date", "to", "tags",
    "industries", "industry", "industry_tags",
}
_COLLECTION_KEYS = (
    "stints", "experience", "experiences", "jobs", "roles", "positions",
    "employment_history", "work_history", "history",
)


def shape_adapter(raw):
    """
    Convert arbitrary raw inputs into minimally valid stints:
    [{company?, title?, start?, end?, tags?}], at least one element.
    """

    def _as_iterable(obj):
        if isinstance(obj, Mapping):
            if any(key in obj for key in _COLLECTION_KEYS):
                for key in _COLLECTION_KEYS:
                    collection = obj.get(key)
                    if collection:
                        return _ensure_sequence(collection)
            if _looks_like_stint(obj):
                return [obj]
            for value in obj.values():
                if value is obj:
                    continue
                nested = _as_iterable(value)
                if nested:
                    return nested
            return []
        if isinstance(obj, Sequence) and not isinstance(obj, (str, bytes, bytearray)):
            return list(obj)
        return []

    def _ensure_sequence(value):
        if value is None:
            return []
        if isinstance(value, Mapping):
            return list(value.values())
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            return list(value)
        return [value]

    def _looks_like_stint(value):
        return isinstance(value, Mapping) and any(k in value for k in _STINT_KEYS)

    def _clean_str(value):
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        try:
            return str(value).strip()
        except Exception:
            return ""

    def _coerce_tags(value):
        if not value:
            return []
        if isinstance(value, (list, tuple, set)):
            parts = [_clean_str(v) for v in value]
        else:
            parts = [_clean_str(part) for part in re.split(r"[;,]", _clean_str(value))]
        seen = set()
        tags: list[str] = []
        for part in parts:
            if not part:
                continue
            token = part.lower()
            if token not in seen:
                seen.add(token)
                tags.append(token)
        return tags

    def _extract_month(token: str) -> Optional[int]:
        for key, mon in _MONTH_MAP.items():
            if key in token:
                return mon
        return None

    def _coerce_date(value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            year = int(value)
            if 1000 <= year <= 2999:
                return f"{year:04d}-01"
            return None
        if isinstance(value, date):
            return f"{value.year:04d}-{value.month:02d}"
        if isinstance(value, str):
            token = value.strip()
            if not token:
                return None
            lowered = token.lower()
            if lowered in _CURRENT_TOKENS:
                return None
            match = _DATE_TOKEN.match(token.replace("/", "-").replace("_", "-"))
            if match:
                year = int(match.group(1))
                month = int(match.group(2) or 1)
                if 1 <= month <= 12:
                    return f"{year:04d}-{month:02d}"
                return None
            digits = re.sub(r"\D", "", token)
            if len(digits) in {6, 8}:
                year = int(digits[:4])
                month = int(digits[4:6])
                if 1 <= month <= 12:
                    return f"{year:04d}-{month:02d}"
            year_match = re.search(r"(19|20)\d{2}", token)
            if year_match:
                year = int(year_match.group())
                month = _extract_month(lowered) or 1
                return f"{year:04d}-{month:02d}"
            return None
        if isinstance(value, Mapping):
            year = value.get("year") or value.get("y")
            month = value.get("month") or value.get("m")
            if year is None:
                return None
            try:
                year_i = int(year)
                month_i = int(month) if month is not None else 1
                month_i = 1 if month_i < 1 else 12 if month_i > 12 else month_i
                return f"{year_i:04d}-{month_i:02d}"
            except Exception:
                return None
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            if not value:
                return None
            try:
                year = int(value[0])
                month = int(value[1]) if len(value) > 1 else 1
                month = 1 if month < 1 else 12 if month > 12 else month
                return f"{year:04d}-{month:02d}"
            except Exception:
                return None
        return None

    def _is_current(entry, end_value):
        if isinstance(end_value, str) and end_value.strip().lower() in _CURRENT_TOKENS:
            return True
        if end_value in (None, "") and entry.get("current") is True:
            return True
        for key in ("is_current", "ongoing", "active"):
            if entry.get(key) is True:
                return True
        return False

    candidates = _as_iterable(raw)
    stints = []
    for entry in candidates:
        if isinstance(entry, Mapping):
            company = _clean_str(entry.get("company") or entry.get("employer") or entry.get("organization") or entry.get("org"))
            title_raw = entry.get("title") or entry.get("role") or entry.get("position") or entry.get("job_title")
            title = normalize_title(_clean_str(title_raw))
            start_raw = entry.get("start") or entry.get("start_date") or entry.get("from")
            end_raw = entry.get("end") or entry.get("end_date") or entry.get("to")
            tags_raw = entry.get("industry_tags") or entry.get("tags") or entry.get("industries") or entry.get("industry")
        else:
            company = ""
            title = normalize_title(_clean_str(entry))
            start_raw = None
            end_raw = None
            tags_raw = None
        start = _coerce_date(start_raw)
        end = None if _is_current(entry if isinstance(entry, Mapping) else {}, end_raw) else _coerce_date(end_raw)
        tags = _coerce_tags(tags_raw)
        company_clean = company or None
        title_clean = title.strip() or None
        if not company_clean and not title_clean:
            continue
        stints.append({
            "company": company_clean,
            "title": title_clean,
            "start": start,
            "end": end,
            "tags": tags,
        })

    if stints:
        return stints

    fallback_title = None
    if isinstance(raw, Mapping):
        for key in ("title", "role", "position", "name", "source"):
            if raw.get(key):
                fallback_title = _clean_str(raw.get(key))
                break
    elif isinstance(raw, str):
        fallback_title = raw.strip()
    if not fallback_title:
        fallback_title = "Experience"

    return [{
        "company": None,
        "title": fallback_title,
        "start": None,
        "end": None,
        "tags": [],
    }]

def normalize_title(title: str) -> str:
    t = (title or "").lower()
    if any(k in t for k in [
        "product designer","ux designer","ui/ux","interaction designer",
        "experience designer","design lead"
    ]):
        return "Product Designer"
    return title or ""

def _to_date(val: str) -> Optional[date]:
    """Accepts 'YYYY-MM'|'YYYY-MM-DD'|'YYYY' and returns date; None if invalid."""
    if not val:
        return None
    try:
        parts = [int(p) for p in str(val).split("-")]
        if len(parts) == 3:
            y, m, d = parts
        elif len(parts) == 2:
            y, m = parts; d = 1
        elif len(parts) == 1:
            y = parts[0]; m = d = 1
        else:
            return None
        return date(y, m, d)
    except Exception:
        return None



def extract_stints(raw):
    stints = []
    for s in raw.get("stints", []):
        start = _to_date(s.get("start"))
        end = _to_date(s.get("end"))
        if end is None:
            end = date.today()
        stints.append({
            "company": s.get("company"),
            "title": s.get("title"),
            "industry": s.get("industry"),
            "start_date": start,
            "end_date": end,
        })
    return stints
