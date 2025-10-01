from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, List, Dict, Any, Optional
from datetime import date

import numpy as np

from .weights import DEFAULT_WEIGHTS
from ..models.embeddings import _cosine as cosine

def _compute_tenure_months(stints):
    """Return month counts for all stints with usable date spans."""
    if not stints:
        return []

    months: list[int] = []

    for stint in stints:
        if not isinstance(stint, dict):
            continue

        start = stint.get("start_date")
        end = stint.get("end_date")

        if not isinstance(start, date):
            continue

        delta = _safe_months_between(start, end)
        if delta <= 0:
            continue

        months.append(delta)

    return months

def _compute_recency_months(stints):
    """Months since the most recent valid end date; None when unknown."""
    if not stints:
        return None

    today = date.today()

    for stint in stints:
        if not isinstance(stint, dict):
            continue

        end = stint.get("end_date")
        start = stint.get("start_date")

        if end is None and isinstance(start, date):
            return 0

        if not isinstance(end, date):
            continue

        months = (today.year - end.year) * 12 + (today.month - end.month)
        if today.day < end.day:
            months -= 1
        return max(months, 0)

    return None


def _cosine(a, b):
    """Compute cosine similarity with strict shape and finiteness checks."""
    a_arr = np.asarray(a, dtype=np.float64)
    b_arr = np.asarray(b, dtype=np.float64)

    if a_arr.ndim != 1:
        raise ValueError(f"expected 1D vector for 'a', got shape {a_arr.shape}")
    if b_arr.ndim != 1:
        raise ValueError(f"expected 1D vector for 'b', got shape {b_arr.shape}")
    if a_arr.shape[0] != b_arr.shape[0]:
        raise ValueError(
            f"cosine requires matching shapes, got {a_arr.shape[0]} and {b_arr.shape[0]} elements"
        )

    if not (np.isfinite(a_arr).all() and np.isfinite(b_arr).all()):
        raise ValueError("cosine received non-finite values")

    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    value = float(np.dot(a_arr, b_arr) / (norm_a * norm_b))
    if value > 1.0:
        return 1.0
    if value < -1.0:
        return -1.0
    return value

def _safe_months_between(a: Optional[date], b: Optional[date]) -> int:
    if not isinstance(a, date):
        return 0

    end = b
    if end is None:
        end = date.today()
    if not isinstance(end, date):
        return 0

    months = (end.year - a.year) * 12 + (end.month - a.month)
    if end.day < a.day:
        months -= 1
    return max(months, 0)

def tenure_scores(stints, min_avg=18, min_last=12):
    months = _compute_tenure_months(stints)
    if not months:
        return 0.0, 0.0, 0.0
    avg = sum(months) / len(months)
    last = months[0]
    avg_score = min(1.0, avg / min_avg) if min_avg else 1.0
    last_score = min(1.0, last / min_last) if min_last else 1.0
    return avg, last, 0.6 * avg_score + 0.4 * last_score

def industry_score(stints, target_tags):
    rel_months = 0; total = 0
    for s in stints:
        m = _safe_months_between(s.get("start_date"), s.get("end_date"))
        total += m
        if any(tag in s.get("industry_tags", []) for tag in target_tags):
            rel_months += m
    return rel_months / total if total else 0.0

def title_match_score(titles: list[tuple[str,int]], target_titles: list[str], target_level: str|None) -> float:
    # Simple fuzzy: 1.0 if any title role matches; small boost if level gap <= 1
    if not titles: return 0.0
    role_match = 0.0
    for role, lvl in titles[:3]:  # last few roles
        if any(t in role for t in target_titles):
            role_match = 1.0
            break
    # Level handling: treat 'senior' as 2, manager 3, etc. Here we default to 2 if unknown.
    tgt_lvl_map = {"ic":2, "senior":2, "manager":3, "lead":3, "director":4, "vp":5}
    tgt_lvl = tgt_lvl_map.get((target_level or "").lower(), 2)
    last_lvl = titles[0][1]
    lvl_gap = abs(last_lvl - tgt_lvl)
    lvl_score = 1.0 if lvl_gap <= 1 else 0.6 if lvl_gap == 2 else 0.3
    return 0.7*role_match + 0.3*lvl_score

EmbedFn = Callable[[str], Any]


def context_penalty(text: str, embed_fn: EmbedFn) -> float:
    # Embedding-based sense disambiguation could be added; here a simple heuristic plus embeddings stub
    if not text: return 0.0
    hiring = embed_fn("Work that involves hiring candidates, owning requisitions, sourcing, interviewing, offers.")
    recruited = embed_fn("Being a job applicant or being recruited by a company.")
    e = embed_fn(text[:2000])
    ch = cosine(e, hiring); cr = cosine(e, recruited)
    return max(0.0, 0.2 if cr > ch else 0.0)

def recency_score(stints, horizon_months=36):
    """Score recency using most recent end date, tolerating missing spans."""
    months_since = _compute_recency_months(stints)
    if months_since is None:
        return 0.0

    if months_since <= 0:
        return 1.0

    if horizon_months:
        horizon = float(horizon_months)
        if months_since <= horizon:
            return max(0.0, 1.0 - (months_since / (horizon * 1.2)))

    return 0.2

def skill_sem_sim(jd_blob: str, cand_blob: str, embed_fn: EmbedFn) -> float:
    if not jd_blob or not cand_blob: return 0.0
    return cosine(embed_fn(jd_blob), embed_fn(cand_blob))


def map_industries_for_stints(stints, companies_tax: dict, keywords_tax: dict):
    for s in stints:
        tags = set(s.get("industry_tags", []))
        comp = (s.get("company") or "").strip()
        if comp and comp in companies_tax:
            tags.update(companies_tax[comp])
        # keyword inference from title + company combined
        blob = f"{s.get('title','')} {s.get('company','')}".lower()
        for tag, kws in keywords_tax.items():
            if any(kw in blob for kw in kws):
                tags.add(tag)
        s["industry_tags"] = sorted(list(tags))
    return stints
