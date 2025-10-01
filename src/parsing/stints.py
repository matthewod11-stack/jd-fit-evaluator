
from datetime import date
from typing import Optional

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
