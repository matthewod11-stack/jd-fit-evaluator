from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Iterable
import json, pathlib, csv

class CanonicalResult(BaseModel):
    candidate_id: str
    fit_score: float = Field(ge=0, le=100)
    rationale: str | None = None
    signals: dict[str, float] = {}

class CanonicalScore(BaseModel):
    artifact: dict
    results: list[CanonicalResult]

class LegacyScore(BaseModel):
    candidate_id: str
    score: float
    explanation: str | None = None

def legacy_to_canonical(legacy: LegacyScore) -> CanonicalScore:
    return CanonicalScore(
        artifact={"version": "canonical-1"},
        results=[CanonicalResult(candidate_id=legacy.candidate_id, fit_score=legacy.score, rationale=legacy.explanation)],
    )

def coerce_to_canonical(obj) -> CanonicalScore:
    if isinstance(obj, dict) and "results" in obj:
        return CanonicalScore.model_validate(obj)
    if isinstance(obj, dict) and {"candidate_id","score"} <= set(obj):
        return legacy_to_canonical(LegacyScore.model_validate(obj))
    raise ValueError("Unrecognized score schema")

def write_scores(items: Iterable[CanonicalScore], out_dir: pathlib.Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    jsonl = out_dir / "scores.jsonl"
    with jsonl.open("w", encoding="utf-8") as f:
        for it in items:
            f.write(it.model_dump_json() + "\n")
    csvp = out_dir / "scores.csv"
    with csvp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id","fit_score","rationale"])
        for it in items:
            for r in it.results:
                w.writerow([r.candidate_id, r.fit_score, (r.rationale or "")[:1000]])