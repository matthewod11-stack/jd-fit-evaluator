import json, hashlib
from pathlib import Path
from typing import List

import requests

from jd_fit_evaluator.config import LLM_MODEL
from .models import Stint

def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

def _ollama_complete(prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": LLM_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
            "format": "json",
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    if "response" not in data:
        raise ValueError("Ollama response missing 'response'")
    return data["response"]

def extract_stints_llm(text: str) -> List[Stint]:
    key = _hash(text)
    cache_path = Path(".cache") / "stints" / f"{key}.json"
    if cache_path.exists():
        try:
            with cache_path.open("r", encoding="utf-8") as cache_file:
                cached_payload = json.load(cache_file)
        except json.JSONDecodeError:
            cached_payload = None
        if isinstance(cached_payload, list):
            try:
                return [Stint.model_validate(item) for item in cached_payload]
            except Exception:
                pass
    prompt = f"""
    You are a resume parser. Return ONLY JSON matching this schema:
    Stint[]: [{{org, title, industry?, start, end?, employment_type?, projects?}}]
    Dates must be ISO-8601 (YYYY-MM-DD). If month/day unknown, use first of month.
    Text:\n{text[:6000]}
    """
    raw = _ollama_complete(prompt)
    def _clean_payload(payload: str) -> str:
        stripped = payload.strip()
        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            stripped = "\n".join(lines).strip()
        if stripped.startswith("json"):
            stripped = stripped[4:].lstrip()
        return stripped

    max_attempts = 3
    errors: list[str] = []
    current_raw = raw
    data = None
    for attempt in range(max_attempts):
        candidate = _clean_payload(current_raw)
        try:
            data = json.loads(candidate)
            raw = current_raw
            break
        except json.JSONDecodeError as exc:
            errors.append(str(exc))
            recovered = False
            for opener, closer in (("[", "]"), ("{", "}")):
                start = candidate.find(opener)
                end = candidate.rfind(closer)
                if start != -1 and end != -1 and end > start:
                    snippet = candidate[start:end + 1]
                    try:
                        data = json.loads(snippet)
                        raw = current_raw
                        recovered = True
                        break
                    except json.JSONDecodeError:
                        continue
            if recovered:
                break
            if attempt == max_attempts - 1:
                break
            hint = (
                f"{prompt}\n\nRespond with VALID JSON only. "
                f"No code fences or commentary. Previous error: {errors[-1]}"
            )
            current_raw = _ollama_complete(hint)
    if data is None:
        raise ValueError(
            f"Failed to parse LLM JSON after {max_attempts} attempts: "
            f"{errors[-1] if errors else 'empty response'}"
        )
    if not isinstance(data, list):
        raise ValueError("LLM response must be a list of stints")
    if hasattr(Stint, "model_validate"):
        stints = [Stint.model_validate(item) for item in data]
    else:
        stints = [Stint.parse_obj(item) for item in data]
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        payload = [stint.model_dump() if hasattr(stint, "model_dump") else stint.dict() for stint in stints]
        with cache_path.open("w", encoding="utf-8") as cache_file:
            json.dump(payload, cache_file)
    except OSError:
        pass
    return stints
