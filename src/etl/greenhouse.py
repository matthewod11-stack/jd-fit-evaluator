
import requests, io, os, time, typing as t, pathlib, json
from datetime import datetime
from ..config import settings
from ..parsing.resume import extract_text

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

TITLE_HINTS = [
    ("recruiter", 2),
    ("technical recruiter", 2),
    ("senior technical recruiter", 2),
    ("talent acquisition", 2),
    ("people operations", 2),
    ("hr operations", 2),
    ("sourcer", 1),
    ("recruiting manager", 3),
]

def guess_titles_norm(text: str) -> list[tuple[str,int]]:
    s = text.lower()
    hits = []
    for key, lvl in TITLE_HINTS:
        if key in s:
            role = "recruiter" if "recruit" in key or "talent" in key else "people_ops"
            hits.append((role, lvl))
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
