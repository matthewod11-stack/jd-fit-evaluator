import string
from functools import lru_cache

import requests

import numpy as np

from src.models.embeddings import get_embedder, _cosine
from src.config import LLM_MODEL

_TITLE_KEY_TRANS = str.maketrans({c: " " for c in string.punctuation})
_TITLE_LOOKUP = {
    "sr product designer": "Product Designer",
    "product designer": "Product Designer",
    "senior product designer": "Product Designer",
    "lead product designer": "Product Designer",
    "principal product designer": "Product Designer",
    "staff product designer": "Product Designer",
    "design lead": "Product Designer",
    "ux designer": "Product Designer",
    "ux design lead": "Product Designer",
    "ux ui designer": "Product Designer",
    "ui ux designer": "Product Designer",
    "ui designer": "Product Designer",
    "interaction designer": "Product Designer",
    "experience designer": "Product Designer",
    "visual designer": "Product Designer",
    "visual designer product": "Product Designer",
    "product design ic5": "Product Designer",
    "ux researcher": "UX Researcher",
    "product manager": "Product Manager",
    "product management": "Product Manager",
    "software engineer": "Software Engineer",
    "senior software engineer": "Software Engineer",
    "full stack engineer": "Software Engineer",
    "frontend engineer": "Software Engineer",
    "front end engineer": "Software Engineer",
    "backend engineer": "Software Engineer",
    "back end engineer": "Software Engineer",
    "data scientist": "Data Scientist",
    "machine learning engineer": "Machine Learning Engineer",
}

TITLE_SIM_THRESHOLD = 0.80
_EMBEDDING_TIE_DELTA = 0.01
_CANONICAL_TITLES = tuple(sorted(set(_TITLE_LOOKUP.values())))
_CANONICAL_TITLE_MAP = {title.lower(): title for title in _CANONICAL_TITLES}

_INDUSTRY_BUCKETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Web3/DeFi",
        (
            "web3",
            "web 3",
            "blockchain",
            "crypto",
            "cryptocurrency",
            "defi",
            "de fi",
            "digital asset",
            "nft",
            "dapp",
            "smart contract",
        ),
    ),
    (
        "FinTech",
        (
            "fintech",
            "financial technology",
            "financial services",
            "payment",
            "payments",
            "banking",
            "lending",
            "wealth management",
            "insurtech",
        ),
    ),
    (
        "E-commerce",
        (
            "e commerce",
            "e-commerce",
            "ecommerce",
            "online retail",
            "retail",
            "marketplace",
            "marketplaces",
            "direct to consumer",
            "d2c",
        ),
    ),
    (
        "Agency",
        (
            "agency",
            "consultancy",
            "consulting",
            "creative agency",
            "design agency",
            "services agency",
        ),
    ),
)

_LLM_ENDPOINT = "http://localhost:11434/api/generate"
_LLM_TIMEOUT = 15


@lru_cache(maxsize=1)
def _get_embedder():
    return get_embedder()


def _to_vector(vector: np.ndarray | list[float] | tuple[float, ...]) -> np.ndarray:
    array = np.asarray(vector, dtype=np.float64)
    if array.ndim == 1:
        result = array
    elif array.ndim == 2 and 1 in array.shape:
        result = array.reshape(-1)
    else:
        raise ValueError(f"Expected 1-D embedding vector, got shape {array.shape}")

    output = np.array(result, dtype=np.float64, copy=True)
    output.setflags(write=False)
    return output


@lru_cache(maxsize=2048)
def _embed_text(text: str) -> np.ndarray:
    embedder = _get_embedder()
    vector = embedder.embed_text(text)
    return _to_vector(vector)


@lru_cache(maxsize=None)
def _canonical_embeddings() -> tuple[tuple[str, np.ndarray], ...]:
    items = []
    for title in _CANONICAL_TITLES:
        normalized = _title_key(title) or title.lower()
        if not normalized:
            continue
        vector = _embed_text(normalized)
        if vector.size == 0:
            continue
        items.append((title, vector))
    return tuple(items)


def _embedding_topk(query: str, k: int = 5) -> list[tuple[str, float]]:
    if not query or k == 0:
        return []

    try:
        query_vec = _embed_text(query)
    except Exception:
        return []

    if query_vec.size == 0:
        return []

    scored: list[tuple[str, float]] = []
    for title, base_vec in _canonical_embeddings():
        if base_vec.shape != query_vec.shape:
            continue
        score = float(_cosine(query_vec, base_vec))
        scored.append((title, score))

    scored.sort(key=lambda pair: pair[1], reverse=True)
    if k is None or k < 0 or k >= len(scored):
        return scored
    return scored[:k]


def _adjudicate_with_llm(query: str, options: list[str] | tuple[str, ...]) -> str | None:
    normalized_query = (query or "").strip()
    normalized_options = tuple(dict.fromkeys(opt for opt in options if opt))
    if not normalized_query or not normalized_options:
        return None
    return _adjudicate_with_llm_cached(normalized_query, normalized_options)


@lru_cache(maxsize=512)
def _adjudicate_with_llm_cached(query: str, options: tuple[str, ...]) -> str | None:
    option_lookup = {opt.lower(): opt for opt in options}
    options_str = ", ".join(options)
    prompt = (
        "You map job titles to canonical categories. "
        f"Valid canonical titles: {options_str}. "
        "Respond with exactly one canonical title from the list that best matches the job title. "
        "If nothing fits, reply with 'Unknown'.\n"
        f"Job title: {query!r}"
    )

    try:
        response = requests.post(
            _LLM_ENDPOINT,
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=_LLM_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    raw_reply = str(data.get("response", "")).strip()
    if not raw_reply:
        return None

    first_line = raw_reply.splitlines()[0].strip().strip("` ")
    first_line = first_line.strip("'\"")
    normalized = first_line.lower().strip(string.punctuation + " ")

    if normalized == "unknown":
        return None

    matched = option_lookup.get(normalized)
    if matched:
        return matched

    fallback = _CANONICAL_TITLE_MAP.get(normalized)
    if fallback in option_lookup.values():
        return fallback
    return None


def _title_key(raw: str | None) -> str:
    if not raw:
        return ""
    lowered = raw.lower().translate(_TITLE_KEY_TRANS)
    return " ".join(lowered.split())


@lru_cache(maxsize=1)
def _industry_keywords() -> tuple[tuple[str, str], ...]:
    items: list[tuple[str, str]] = []
    for bucket, keywords in _INDUSTRY_BUCKETS:
        for keyword in keywords:
            normalized = _title_key(keyword)
            if not normalized:
                continue
            items.append((normalized, bucket))
    items.sort(key=lambda pair: (-len(pair[0]), pair[1]))
    return tuple(items)


def normalize_title(raw: str) -> str:
    key = _title_key(raw)
    if not key:
        return ""
    mapped = _TITLE_LOOKUP.get(key)
    if mapped:
        return mapped
    candidates = _embedding_topk(key)
    if candidates:
        best_title, best_score = candidates[0]
        if best_score >= TITLE_SIM_THRESHOLD:
            ambiguous_titles = [
                title
                for title, score in candidates
                if abs(score - best_score) <= _EMBEDDING_TIE_DELTA
            ]
            if len(ambiguous_titles) > 1:
                adjudicated = _adjudicate_with_llm(raw or key, ambiguous_titles)
                if adjudicated:
                    return adjudicated
            return best_title
    return raw.strip()


def normalize_industry(raw: str) -> str:
    key = _title_key(raw)
    if not key:
        return ""

    padded = f" {key} "
    for keyword, bucket in _industry_keywords():
        needle = f" {keyword} "
        if needle in padded:
            return bucket

    cleaned = raw.strip()
    return cleaned if not cleaned else "Other"
