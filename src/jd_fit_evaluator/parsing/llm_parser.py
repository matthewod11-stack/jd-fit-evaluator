from pydantic import BaseModel
from typing import List
from jd_fit_evaluator.models.llm import get_llm

class Stint(BaseModel):
    title: str
    company: str|None=None
    start: str|None=None
    end: str|None=None
    responsibilities: List[str]=[]

class ParsedResume(BaseModel):
    name: str|None=None
    emails: List[str]=[]
    phones: List[str]=[]
    stints: List[Stint]=[]
    skills: List[str]=[]
    education: List[str]=[]

def parse_resume_with_llm(text: str) -> ParsedResume:
    llm = get_llm()
    resp = llm.chat_json(
        "Extract resume JSON",
        f"Resume:\n{text[:6000]}\nReturn JSON with keys: name, emails[], phones[], stints[{ { 'title': '', 'company': '', 'start': '', 'end': '', 'responsibilities': [] } }], skills[], education[]",
        schema_hint="resume"
    )
    return ParsedResume.model_validate(resp.parsed_json or {})