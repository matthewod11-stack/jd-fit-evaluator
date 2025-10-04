from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Iterable
import json, pathlib, csv

class CanonicalResult(BaseModel):
    candidate_id: str
    fit_score: float = Field(ge=0, le=100)
    rationale: str | None = None
    signals: dict[str, float] = {}
    # Additional fields for CSV output
    name: str = ""
    email: str = ""
    title_canonical: str = ""
    industry_canonical: str = ""

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
    
    # Convert to list so we can iterate multiple times
    items_list = list(items)

    # Backwards compatibility: if callers pass a flat list of CanonicalResult
    # (refactor changed score_candidates to return flat lists), wrap them into
    # a single CanonicalScore artifact so downstream code and tests continue
    # to work without immediate changes.
    if items_list:
        first = items_list[0]
        # If first is a CanonicalResult, wrap the list
        if isinstance(first, CanonicalResult):
            # items_list currently holds CanonicalResult instances; wrap into a CanonicalScore
            canonical_results = list(items_list)
            items_list = [CanonicalScore(artifact={"version": "canonical-1", "role": "unknown"}, results=canonical_results)]
    
    jsonl = out_dir / "scores.jsonl"
    with jsonl.open("w", encoding="utf-8") as f:
        for it in items_list:
            f.write(it.model_dump_json() + "\n")
    
    # Generate rationales.md if rationale data exists
    rationales_file = out_dir / "rationales.md"
    with rationales_file.open("w", encoding="utf-8") as f:
        for it in items_list:
            for r in it.results:
                if r.rationale:
                    f.write(f"# {r.candidate_id}\n\n{r.rationale}\n\n")
    
    csvp = out_dir / "scores.csv"
    with csvp.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "candidate_id", "name", "email", "title_canonical", "industry_canonical",
            "score", "titles_score", "industry_score", "tenure_score", "skills_score", "context_score"
        ])
        for it in items_list:
            for r in it.results:
                w.writerow([
                    r.candidate_id,
                    r.name,
                    r.email,
                    r.title_canonical,
                    r.industry_canonical,
                    r.fit_score,
                    r.signals.get("title", 0.0),
                    r.signals.get("industry", 0.0),
                    r.signals.get("tenure", 0.0),
                    r.signals.get("skills", 0.0),
                    r.signals.get("context", 0.0)
                ])