import io, re, typing as t
from pdfminer.high_level import extract_text as pdf_extract
import docx

def extract_text(filename: str, data: bytes) -> str:
    fn = filename.lower()
    if fn.endswith('.pdf'):
        return pdf_extract(io.BytesIO(data))
    if fn.endswith(('.doc', '.docx')):
        doc = docx.Document(io.BytesIO(data))
        return '\n'.join(p.text for p in doc.paragraphs)
    try:
        return data.decode('utf-8', errors='ignore')
    except Exception:
        return ''

LEVEL_MAP = {
  "intern": 0, "junior": 1, "associate": 1, "sr": 2, "senior": 2,
  "lead": 3, "manager": 3, "principal": 4, "director": 4, "head": 4, "vp": 5
}

def normalize_title(raw: str) -> tuple[str,int]:
    s = raw.lower()
    level = max((lvl for k,lvl in LEVEL_MAP.items() if k in s), default=2)
    if "recruit" in s or "talent" in s:
        role = "recruiter"
    elif "people ops" in s or "hr operations" in s or "people operations" in s:
        role = "people_ops"
    else:
        role = "other"
    return role, level
