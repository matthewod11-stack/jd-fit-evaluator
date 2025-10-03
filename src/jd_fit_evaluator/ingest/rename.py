import re
from pathlib import Path
from jd_fit_evaluator.models.llm import get_llm

def extract_candidate_name(text: str) -> str | None:
    m = re.search(r'([A-Z][a-z]+)\s+([A-Z][a-z]+)', text)
    if m:
        return f"{m.group(2)}, {m.group(1)}"
    llm = get_llm()
    resp = llm.chat_json("Extract person name", f"Resume text snippet:\n{text[:500]}\nReturn JSON: {{'name':'Last, First'}}", schema_hint="name")
    return (resp.parsed_json or {}).get("name")

def normalize_filename(in_path: Path, name: str) -> Path:
    safe = re.sub(r'[^A-Za-z0-9,_\-]+', '_', name).strip('_')
    return in_path.with_name(f"{safe}_{in_path.stem[:6]}{in_path.suffix.lower()}")

def batch_rename(dir_in: str):
    p = Path(dir_in)
    renames = []
    for f in p.glob("**/*"):
        if f.suffix.lower() not in {".pdf",".docx",".txt"}: continue
        text = f.read_text(errors="ignore")[:1000]
        name = extract_candidate_name(text or f.stem) or f.stem
        out = normalize_filename(f, name)
        if out != f:
            f.rename(out)
            renames.append((f, out))
    return renames