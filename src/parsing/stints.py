
import re
from datetime import datetime
from typing import List, Dict

# Common date formats like "Jan 2021 - Mar 2023", "2020–Present", etc.
DATE_RGX = re.compile(
    r'(?P<start>(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4})\s*[-–—]\s*(?P<end>(Present|Now|Current|(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4}))',
    re.IGNORECASE
)

# Simplistic company/title heuristics near date ranges
TITLE_HINT = re.compile(r'(Senior|Sr\.?|Lead|Principal|Manager|Director|Head)?\s*([A-Z][A-Za-z\-/& ]{2,40})', re.IGNORECASE)

def parse_month_year(tok: str):
    tok = tok.strip()
    if re.match(r'\d{4}$', tok):
        return {"year": int(tok), "month": 1, "day": 1}
    try:
        dt = datetime.strptime(tok[:3].title() + " " + re.search(r'\d{4}', tok).group(0), "%b %Y")
        return {"year": dt.year, "month": dt.month, "day": 1}
    except Exception:
        return None

def extract_stints(resume_text: str) -> List[Dict]:
    lines = resume_text.splitlines()
    stints = []
    for i, line in enumerate(lines):
        m = DATE_RGX.search(line)
        if not m:
            continue
        start_raw = m.group('start'); end_raw = m.group('end')
        start = parse_month_year(start_raw)
        end = None if re.match(r'(?i)present|now|current', end_raw) else parse_month_year(end_raw)

        # Look around the date line for company/title hints (previous & next lines)
        window = " ".join(lines[max(0, i-2):min(len(lines), i+3)])
        # naive title/company split: first capitalized phrase as title, next as company
        title = None; company = None
        # Try to capture a "Title at Company" pattern
        m2 = re.search(r'(?P<title>[A-Z][A-Za-z\-/& ]{2,60})\s+(at|@)\s+(?P<company>[A-Z][A-Za-z0-9\-/&\. ]{2,60})', window)
        if m2:
            title = m2.group('title').strip()
            company = m2.group('company').strip()
        else:
            # fallback: two consecutive capitalized phrases
            caps = re.findall(r'([A-Z][A-Za-z0-9\-/&\. ]{2,60})', window)
            if caps:
                title = caps[0].strip()
                if len(caps) > 1:
                    company = caps[1].strip()

        if not title and not company:
            continue

        stints.append({
            "title": (title or "").strip(),
            "company": (company or "").strip(),
            "start": start,
            "end": end,
            "industry_tags": [],
        })

    # Deduplicate similar stints
    uniq = []
    seen = set()
    for s in stints:
        key = (s.get("title","").lower(), s.get("company","").lower(), (s.get("start") or {}).get("year"))
        if key in seen: 
            continue
        seen.add(key); uniq.append(s)
    # Sort by start desc
    uniq.sort(key=lambda s: (s.get("start") or {}).get("year", 0)*12 + (s.get("start") or {}).get("month",0), reverse=True)
    return uniq[:12]  # cap
