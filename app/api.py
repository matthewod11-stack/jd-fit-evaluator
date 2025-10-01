from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from ..src.scoring.finalize import compute_fit

app = FastAPI(title="JD Fit Evaluator API")

class Role(BaseModel):
    titles: list[str]
    level: str
    industries: list[str]
    jd_skills_blob: str
    min_avg_months: int = 18
    min_last_months: int = 12

class Candidate(BaseModel):
    name: str
    titles_norm: list[tuple[str,int]] = []
    stints: list[dict] = []
    skills_blob: str = ""
    relevant_bullets_blob: str = ""
    bonus_flags: list[float] | None = None

@app.post("/score")
def score(role: Role, candidate: Candidate):
    return compute_fit(candidate.model_dump(), role.model_dump())
