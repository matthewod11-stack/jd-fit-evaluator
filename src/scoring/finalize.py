from __future__ import annotations
from typing import Dict, Any
from .features import (
    title_match_score, industry_score, tenure_scores, recency_score,
    context_penalty, skill_sem_sim
)
from .weights import DEFAULT_WEIGHTS

def compute_fit(candidate: dict, role: dict, weights: dict | None = None) -> dict:
    W = (weights or DEFAULT_WEIGHTS).copy()

    titles = candidate.get("titles_norm", [])  # [(role, level)]
    tscore = title_match_score(titles, role.get("titles", []), role.get("level"))

    iscore = industry_score(candidate.get("stints", []), role.get("industries", []))

    jd_blob = role.get("jd_skills_blob", "")
    cand_blob = (candidate.get("skills_blob", "") + "\n" + candidate.get("relevant_bullets_blob", "")).strip()
    sscore = skill_sem_sim(jd_blob, cand_blob)

    cpen = context_penalty(candidate.get("relevant_bullets_blob", ""))
    cscore = max(0.0, 1.0 - cpen)

    avg, last, ten = tenure_scores(candidate.get("stints", []),
                                   role.get("min_avg_months", 18),
                                   role.get("min_last_months", 12))

    rscore = recency_score(candidate.get("stints", []))

    bscore = min(0.1, sum(candidate.get("bonus_flags", []))) if candidate.get("bonus_flags") else 0.0

    total = (
        W["title"]*tscore +
        W["industry"]*iscore +
        W["skills"]*sscore +
        W["context"]*cscore +
        W["tenure"]*ten +
        W["recency"]*rscore +
        W["bonus"]*bscore
    )
    fit = round(100*total, 1)

    why = [
        f"Titles match score: {tscore:.2f} (last level gap soft-penalized)",
        f"Industry relevance: {iscore:.2f}",
        f"Skills semantic sim: {sscore:.2f}",
        f"Context alignment: {cscore:.2f}",
        f"Tenure (avg {avg:.1f} mo, last {last:.1f} mo): {ten:.2f}",
        f"Recency: {rscore:.2f}",
    ]
    return {"fit": fit, "subs": {
        "title": tscore, "industry": iscore, "skills": sscore, "context": cscore,
        "tenure": ten, "recency": rscore, "bonus": bscore
    }, "why": why}
