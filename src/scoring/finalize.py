from __future__ import annotations
from typing import Dict, Any
from datetime import datetime, timezone
import json
from pathlib import Path

import numpy as np

from .features import (
    title_match_score, industry_score, tenure_scores, recency_score,
    context_penalty, skill_sem_sim
)
from .weights import DEFAULT_WEIGHTS
from jd_fit_evaluator.models.embeddings import get_embedder
from jd_fit_evaluator.utils.schema import CanonicalScore, CanonicalResult

def compute_fit(candidate: dict, role: dict, weights: dict | None = None) -> dict:
    W = (weights or DEFAULT_WEIGHTS).copy()

    embedder = get_embedder()
    _embed_cache: dict[str, np.ndarray] = {}

    def _embed(text: str) -> np.ndarray:
        key = text or ""
        cached = _embed_cache.get(key)
        if cached is not None:
            return cached

        vector = embedder.embed_text(key)
        array = np.asarray(vector, dtype=np.float64)
        if array.ndim == 1:
            result = array
        elif array.ndim == 2 and 1 in array.shape:
            result = array.reshape(-1)
        else:
            raise ValueError(f"Expected 1-D embedding vector, got shape {array.shape}")

        result = np.array(result, dtype=np.float64, copy=True)
        _embed_cache[key] = result
        return result

    titles = candidate.get("titles_norm", [])  # [(role, level)]
    tscore = title_match_score(titles, role.get("titles", []), role.get("level"))

    iscore = industry_score(candidate.get("stints", []), role.get("industries", []))

    jd_blob = role.get("jd_skills_blob", "")
    cand_blob = (candidate.get("skills_blob", "") + "\n" + candidate.get("relevant_bullets_blob", "")).strip()
    sscore = skill_sem_sim(jd_blob, cand_blob, _embed)

    cpen = context_penalty(candidate.get("relevant_bullets_blob", ""), _embed)
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


def _evidence(snippet_pool: list[str], *needles: str, default: str = "(no direct snippet)"):
    s = " ".join(snippet_pool).lower()
    for n in needles:
        if n and n.lower() in s:
            return n
    return default

def build_rationale(features, jd_terms: list[str], resume_terms: list[str]) -> list[str]:
    return [
      f"Has recent Web3/DeFi stint (≤3y): evidence '{_evidence(resume_terms, 'defi','web3','protocol')}'",
      f"Wallet/smart contract exposure: evidence '{_evidence(resume_terms, 'wallet','smart contract','metamask')}'",
      f"Usability testing experience: evidence '{_evidence(resume_terms, 'usability testing','user research')}'",
      f"Title aligned to Product/UX Designer: score={features.get('title_score',0)}",
    ]


def score_candidates(parsed_candidates: list[dict], role: str | dict, explain: bool = False) -> list[CanonicalResult]:
    """
    Score parsed candidates against a role definition.

    Args:
        parsed_candidates: List of dicts with 'path' and 'parsed' keys (or just parsed candidate dicts)
        role: Either a role name/path string or a role dict with scoring criteria
        explain: If True, include detailed rationale in results

    Returns:
        List[CanonicalResult] — flat list of candidate scoring results (no artifact wrapper)
    """
    # Load role definition
    if isinstance(role, str):
        role_dict = _load_role(role)
    else:
        role_dict = role

    # Extract weights from role if present
    weights = role_dict.get("weights")

    results = []
    for item in parsed_candidates:
        # Handle both formats: {"path": ..., "parsed": ...} or just the parsed dict
        if isinstance(item, dict) and "parsed" in item:
            candidate = item["parsed"]
            # Prefer candidate_id from data, fallback to filename
            candidate_id = candidate.get("candidate_id") or Path(item["path"]).stem
        else:
            candidate = item
            candidate_id = candidate.get("candidate_id", candidate.get("name", "unknown"))

        # Compute fit score
        fit_result = compute_fit(candidate, role_dict, weights)

        # Build rationale if requested
        rationale = None
        if explain and fit_result.get("why"):
            rationale = "\n".join(fit_result["why"])

        # Extract metadata for CSV
        name = candidate.get("name", "")
        emails = candidate.get("emails", [])
        email = emails[0] if emails else ""

        # Extract most recent title and industry from stints
        stints = candidate.get("stints", [])
        title_canonical = ""
        industry_canonical = ""
        if stints:
            latest_stint = stints[0]
            title_canonical = latest_stint.get("title", "")
            industry_canonical = latest_stint.get("industry", "")

        # Create canonical result
        result = CanonicalResult(
            candidate_id=candidate_id,
            fit_score=fit_result["fit"],
            rationale=rationale,
            signals=fit_result.get("subs", {}),
            name=name,
            email=email,
            title_canonical=title_canonical,
            industry_canonical=industry_canonical
        )
        results.append(result)

    # Return flat list of results (was previously wrapped in a CanonicalScore artifact)
    return results


def _load_role(role: str) -> dict:
    """Load role definition from file or built-in profiles."""
    from .jd_profile import AGORIC_SENIOR_PRODUCT_DESIGNER, JD_PD_WEB3

    # Check if it's a built-in profile
    if role.lower() in {"agoric", "senior_product_designer", "product_designer"}:
        return AGORIC_SENIOR_PRODUCT_DESIGNER
    if role.lower() in {"pd_web3", "web3"}:
        return JD_PD_WEB3

    # Try loading from file
    role_path = Path(role)
    if role_path.exists():
        with role_path.open() as f:
            data = json.load(f)
            # Handle the format from data/profiles/product.json
            if "jd" in data and "weights" in data:
                return data
            return data

    # Fallback to default
    return AGORIC_SENIOR_PRODUCT_DESIGNER
