"""
DEPRECATED (2025-10-01): Greenhouse Harvest ingestion is paused for MVP.
Use file-based ingestion via tools/split_resumes_and_manifest.py and manifest CSV.
"""
import requests, io, os, time, typing as t, pathlib, json, csv
from datetime import datetime, date
from functools import lru_cache
from ..parsing.stints import shape_adapter
from ..config import settings
from ..parsing.resume import extract_text

MONTH_LOOKUP = {
    k: v for v, k in enumerate([
        "", "jan", "feb", "mar", "apr", "may", "jun",
        "jul", "aug", "sep", "oct", "nov", "dec"
    ]) if k
}
MONTH_LOOKUP.update({
    k: v for v, k in enumerate([
        "", "january", "february", "march", "april", "may", "june",
        "july", "august", "september", "october", "november", "december"
    ]) if k
})


def _as_path(value) -> pathlib.Path | None:
    if isinstance(value, pathlib.Path):
        return value
    if isinstance(value, (str, os.PathLike)):
        try:
            p = pathlib.Path(value).expanduser()
        except Exception:
            return None
        return p
    return None


@lru_cache(maxsize=8)
def _load_manifest_rows(manifest_path: pathlib.Path) -> dict[str, dict[str, str]]:
    if not manifest_path or not manifest_path.exists():
        return {}
    try:
        with manifest_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows: dict[str, dict[str, str]] = {}
            for row in reader:
                cid = (row.get("candidate_id") or "").strip()
                if cid:
                    rows[cid] = row
            return rows
    except Exception:
        return {}


def _decode_manifest_stints(payload) -> list[dict]:
    if not payload:
        return []
    if isinstance(payload, list):
        return [p for p in payload if isinstance(p, dict)]
    if isinstance(payload, dict):
        if "stints" in payload and isinstance(payload["stints"], list):
            return [p for p in payload["stints"] if isinstance(p, dict)]
        return [payload]
    if isinstance(payload, (str, bytes)):
        text = payload.decode() if isinstance(payload, bytes) else payload
        text = text.strip()
        if not text:
            return []
        if text.startswith("{") or text.startswith("["):
            try:
                loaded = json.loads(text)
            except Exception:
                return []
            return _decode_manifest_stints(loaded)
        # Fallback: simple pipe-delimited rows "title|company|start|end"
        rows = []
        for line in text.splitlines():
            parts = [p.strip() for p in line.split("|")]
            if not any(parts):
                continue
            row = {}
            if len(parts) > 0:
                row["title"] = parts[0] or None
            if len(parts) > 1:
                row["company"] = parts[1] or None
            if len(parts) > 2:
                row["start"] = parts[2] or None
            if len(parts) > 3:
                row["end"] = parts[3] or None
            rows.append(row)
        return rows
    return []


def _extract_manifest_stints(candidate_ref) -> list[dict]:
    """Pull stint rows from a manifest payload or file reference if present."""
    # Direct dict/list payloads
    if isinstance(candidate_ref, dict):
        for key in ("manifest_stints", "stints", "experience", "raw_stints"):
            val = candidate_ref.get(key)
            stints = _decode_manifest_stints(val)
            if stints:
                return stints
        # Manifest reference on disk
        manifest_path = candidate_ref.get("manifest_path") or candidate_ref.get("manifest")
        candidate_id = candidate_ref.get("candidate_id") or candidate_ref.get("id")
        if manifest_path and candidate_id:
            path = _as_path(manifest_path)
            if path:
                rows = _load_manifest_rows(path)
                row = rows.get(str(candidate_id))
                if row:
                    for key in ("stints_json", "stints", "experience", "notes"):
                        stints = _decode_manifest_stints(row.get(key))
                        if stints:
                            return stints
        # Inline manifest row
        if "manifest_row" in candidate_ref and isinstance(candidate_ref["manifest_row"], dict):
            row = candidate_ref["manifest_row"]
            for key in ("stints_json", "stints", "experience", "notes"):
                stints = _decode_manifest_stints(row.get(key))
                if stints:
                    return stints
    # Path (JSON w/ stints)
    path = _as_path(candidate_ref)
    if path and path.exists():
        try:
            if path.suffix.lower() in {".json", ".ndjson"}:
                data = json.loads(path.read_text())
                if isinstance(data, dict):
                    for key in ("manifest_stints", "stints", "experience"):
                        stints = _decode_manifest_stints(data.get(key))
                        if stints:
                            return stints
        except Exception:
            return []
    # Maybe JSON encoded string
    if isinstance(candidate_ref, str):
        candidate_ref = candidate_ref.strip()
        if candidate_ref.startswith("{") or candidate_ref.startswith("["):
            try:
                data = json.loads(candidate_ref)
            except Exception:
                data = None
            if isinstance(data, dict):
                for key in ("manifest_stints", "stints", "experience"):
                    stints = _decode_manifest_stints(data.get(key))
                    if stints:
                        return stints
    return []


def _parse_date(value) -> date | None:
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, dict):
        year = value.get("year") or value.get("y")
        month = value.get("month") or value.get("m") or 1
        day = value.get("day") or value.get("d") or 1
        try:
            return date(int(year), int(month) if month else 1, int(day) if day else 1)
        except Exception:
            return None
    if isinstance(value, (int, float)):
        try:
            year = int(value)
        except Exception:
            return None
        if 1900 <= year <= 2100:
            return date(year, 1, 1)
        return None
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return None
        lower = raw.lower()
        if lower in {"present", "current", "ongoing", "now"}:
            return None
        cleaned = raw.replace("/", " ").replace("-", " ").replace(",", " ")
        tokens = [t for t in cleaned.split() if t]
        year = None
        month = None
        day = None
        for tok in tokens:
            tok_lower = tok.lower()
            if tok_lower in MONTH_LOOKUP and not month:
                month = MONTH_LOOKUP[tok_lower]
                continue
            if tok.isdigit():
                val = int(tok)
                if len(tok) == 4 and 1900 <= val <= 2100:
                    year = val
                elif not month and 1 <= val <= 12:
                    month = val
                elif not day and 1 <= val <= 31:
                    day = val
        if year is None:
            # Last chance: try YYYYMM or YYYYMMDD
            digits = "".join(ch for ch in tokens if ch.isdigit())
            if len(digits) == 6:
                year = int(digits[:4])
                month = int(digits[4:6])
            elif len(digits) == 8:
                year = int(digits[:4])
                month = int(digits[4:6])
                day = int(digits[6:8])
        if not year:
            return None
        month = month or 1
        day = day or 1
        try:
            return date(year, max(1, min(12, month)), max(1, min(28 if month == 2 else 30 if month in {4, 6, 9, 11} else 31, day)))
        except Exception:
            return None
    return None


def _normalize_tags(value) -> list[str]:
    if not value:
        return []
    if isinstance(value, (list, tuple, set)):
        return sorted({str(v).strip().lower() for v in value if str(v).strip()})
    if isinstance(value, str):
        parts = [p.strip().lower() for p in value.replace(";", ",").split(",")]
        return sorted({p for p in parts if p})
    return []


def _stint_sort_key(stint: dict):
    end = stint.get("end_date") or date.today()
    start = stint.get("start_date") or end
    return (end, start)


def _normalize_stints(stints: list[dict]) -> list[dict]:
    norm: list[dict] = []
    for stint in stints:
        if not isinstance(stint, dict):
            continue
        title = (stint.get("title") or stint.get("role") or "").strip()
        company = (stint.get("company") or stint.get("employer") or "").strip()
        start = _parse_date(stint.get("start") or stint.get("start_date") or stint.get("from"))
        end_value = stint.get("end") or stint.get("end_date") or stint.get("to")
        end = _parse_date(end_value)
        if isinstance(end_value, str) and end_value.strip().lower() in {"present", "current", "ongoing", "now"}:
            end = None
        if stint.get("current") is True:
            end = None
        tags = _normalize_tags(stint.get("industry_tags") or stint.get("tags") or stint.get("industries"))
        if not title and not company:
            continue
        norm.append({
            "company": company or None,
            "title": title or None,
            "start_date": start,
            "end_date": end,
            "industry_tags": tags,
        })
    if not norm:
        return []
    norm.sort(key=_stint_sort_key, reverse=True)
    return norm


def _fallback_stints(candidate_ref) -> list[dict]:
    payload = candidate_ref if isinstance(candidate_ref, dict) else {"source": candidate_ref}
    try:
        raw = shape_adapter(payload)
    except NotImplementedError:
        raw = []
    except Exception:
        raw = []
    normalized = _normalize_stints(raw)
    if normalized:
        return normalized
    return [{
        "company": None,
        "title": "Experience",
        "start_date": None,
        "end_date": None,
        "industry_tags": [],
    }]


def get_stints(candidate_ref):
    """Return a non-empty list of normalized stints for ``candidate_ref``."""
    manifest_stints = _normalize_stints(_extract_manifest_stints(candidate_ref))
    if manifest_stints:
        return manifest_stints
    return _fallback_stints(candidate_ref)

GH_API = "https://harvest.greenhouse.io/v1"

def gh_auth():
    token = settings.gh_token or ""
    return (token, "")

def list_applications(job_id: str, per_page: int = 100) -> list[dict]:
    apps = []
    page = 1
    while True:
        r = requests.get(
            f"{GH_API}/applications",
            params={"job_id": job_id, "per_page": per_page, "page": page},
            auth=gh_auth()
        )
        if r.status_code == 429:
            time.sleep(2); continue
        r.raise_for_status()
        batch = r.json()
        if not batch: break
        apps.extend(batch)
        page += 1
    return apps

def get_candidate(cid: int) -> dict:
    r = requests.get(f"{GH_API}/candidates/{cid}", auth=gh_auth())
    r.raise_for_status()
    return r.json()

def list_attachments(cid: int) -> list[dict]:
    r = requests.get(f"{GH_API}/candidates/{cid}/attachments", auth=gh_auth())
    r.raise_for_status()
    return r.json()

def download_attachment(aid: int) -> tuple[str, bytes]:
    # First try the documented download; allow redirects
    url = f"{GH_API}/attachments/{aid}/download"
    r = requests.get(url, auth=gh_auth(), allow_redirects=True)
    r.raise_for_status()
    # Try to infer a filename if present in headers
    fname = None
    cd = r.headers.get("content-disposition", "")
    if "filename=" in cd:
        fname = cd.split("filename=")[-1].strip().strip('"')
    if not fname:
        fname = f"attachment_{aid}.bin"
    return fname, r.content

# --- light heuristics to normalize candidate for scoring ---

TITLE_HINTS = {
    "product_designer": [
        "product designer","senior product designer","ux designer",
        "senior ux designer","ui/ux designer","interaction designer",
        "design lead","experience designer"
    ],
    "web3_design_signals": [
        "defi","web3","crypto","blockchain","wallet","smart contract",
        "protocol","metamask","uniswap","aave","lido","staking","dapp"
    ],
    # legacy keys may remain if referenced elsewhere
}

def guess_titles_norm(text: str) -> list[tuple[str,int]]:
    s = text.lower()
    hits = []
    
    # Check for product designer signals
    if "product_designer" in TITLE_HINTS:
        for keyword in TITLE_HINTS["product_designer"]:
            if keyword in s:
                hits.append(("product_designer", 3))
                break
    
    # Check for web3 design signals
    if "web3_design_signals" in TITLE_HINTS:
        web3_count = sum(1 for keyword in TITLE_HINTS["web3_design_signals"] if keyword in s)
        if web3_count > 0:
            hits.append(("web3_experience", min(web3_count, 3)))
    
    # de-dup preserve order
    seen = set(); out = []
    for h in hits:
        if h not in seen:
            out.append(h); seen.add(h)
    return out[:3] if out else []

def normalize_candidate(gh_cand: dict, resume_filename: str|None, resume_bytes: bytes|None) -> dict:
    name = gh_cand.get("first_name","") + " " + gh_cand.get("last_name","")
    resume_text = ""
    if resume_bytes is not None and resume_filename:
        try:
            resume_text = extract_text(resume_filename, resume_bytes)
        except Exception:
            resume_text = ""

    titles_norm = guess_titles_norm(resume_text)
    stints = extract_stints_from_resume(resume_text)
    stints = enrich_industries(stints)
    skills_blob = resume_text[:4000]
    relevant_bullets_blob = resume_text[:8000]
    return {
        "name": name.strip() or f"candidate_{gh_cand.get('id')}",
        "candidate_id": gh_cand.get("id"),
        "email": (gh_cand.get("email_addresses") or [{}])[0].get("value"),
        "titles_norm": titles_norm,
        "stints": stints,
        "skills_blob": skills_blob,
        "relevant_bullets_blob": relevant_bullets_blob,
        "source": "greenhouse",
        "ingested_at": datetime.utcnow().isoformat() + "Z",
    }

def ingest_job(job_id: str, out_dir: str = "data/ingest") -> list[str]:
    outp = pathlib.Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    wrote = []
    apps = list_applications(job_id)
    for app in apps:
        cid = app.get("candidate_id")
        if not cid: continue
        gh_cand = get_candidate(cid)
        # Fetch resume-like attachment if present
        resume_name, resume_bytes = None, None
        try:
            atts = list_attachments(cid)
        except Exception:
            atts = []
        for a in atts:
            # Greenhouse marks 'type' or 'filename'
            atype = (a.get("type") or "").lower()
            fname = a.get("filename") or ""
            if "resume" in atype or fname.lower().endswith((".pdf",".doc",".docx",".txt")):
                try:
                    dn, db = download_attachment(a["id"])
                    resume_name, resume_bytes = dn or fname, db
                    break
                except Exception:
                    continue
        cand_norm = normalize_candidate(gh_cand, resume_name, resume_bytes)
        fp = outp / f"{cid}.json"
        fp.write_text(json.dumps(cand_norm, indent=2))
        wrote.append(str(fp))
    return wrote


# --- taxonomy assisted enrichment ---
def _load_taxonomy():
    base = pathlib.Path("data/taxonomy")
    companies = {}
    keywords = {}
    try:
        companies = json.loads((base/"companies.json").read_text())
    except Exception:
        pass
    try:
        keywords = json.loads((base/"industries.json").read_text())
    except Exception:
        pass
    return companies, keywords

def extract_stints_from_resume(text: str):
    try:
        from ..parsing.stints import extract_stints as _extract
        return _extract(text)
    except Exception:
        return []

def enrich_industries(stints):
    companies, keywords = _load_taxonomy()
    from ..scoring.features import map_industries_for_stints
    return map_industries_for_stints(stints, companies, keywords)
