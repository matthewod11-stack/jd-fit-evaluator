from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests
from jinja2 import Template

from jd_fit_evaluator.config import LLM_MODEL

from .jd_profile import JD_PD_WEB3

_POSITIVE_HINTS = ("strength", "positive", "match", "met", "aligned", "present", "advantage")
_NEGATIVE_HINTS = ("gap", "missing", "lack", "anti", "risk", "concern", "flag", "weak")
_EVIDENCE_HINTS = ("evidence", "snippet", "example", "note", "proof", "quote", "detail", "source")
_HIGH_SCORE = 0.65
_LOW_SCORE = 0.35
_MAX_ITEMS = 6


def _summarize_signals(signals: Mapping[str, Any] | None) -> tuple[str, str, str]:
    if not isinstance(signals, Mapping) or not signals:
        return ("None noted", "None noted", "None provided")

    strengths: list[str] = []
    gaps: list[str] = []
    evidence: list[str] = []

    def _format_score(value: float) -> str:
        txt = f"{value:.2f}".rstrip("0").rstrip(".")
        return txt or "0"

    def _humanize(label: str) -> str:
        cleaned = " ".join(label.replace("-", " ").replace("_", " ").split())
        return cleaned.strip()

    def _classify(key: str) -> str | None:
        lower = key.lower()
        if any(hint in lower for hint in _EVIDENCE_HINTS):
            return "evidence"
        if any(hint in lower for hint in _NEGATIVE_HINTS):
            return "gaps"
        if any(hint in lower for hint in _POSITIVE_HINTS):
            return "strengths"
        return None

    def _coerce_scalar(raw: Any) -> float | None:
        if isinstance(raw, bool):
            return 1.0 if raw else 0.0
        if isinstance(raw, (int, float)):
            return float(raw)
        if isinstance(raw, str):
            text = raw.strip().lower()
            if text in {"true", "yes", "present", "met"}:
                return 1.0
            if text in {"false", "no", "missing"}:
                return 0.0
            try:
                return float(raw)
            except ValueError:
                return None
        return None

    def _score_from_mapping(data: Mapping[str, Any]) -> float | None:
        for key in ("score", "value", "confidence", "weight", "met", "present", "match"):
            if key in data:
                score = _coerce_scalar(data[key])
                if score is not None:
                    return score
        return None

    def _add(target: list[str], text: str) -> None:
        if len(target) >= _MAX_ITEMS:
            return
        entry = text.strip()
        if entry and entry not in target:
            target.append(entry)

    snippet_keys = set(_EVIDENCE_HINTS)

    def _process(key: str, value: Any, hint: str | None = None) -> None:
        if value is None:
            return

        category = hint or _classify(key or "")

        if isinstance(value, Mapping):
            label = value.get("label") or value.get("name") or value.get("term") or _humanize(key or "")
            score = _score_from_mapping(value)
            snippet = None
            for snippet_key in snippet_keys:
                if snippet_key in value:
                    snippet = value[snippet_key]
                    break
            if snippet:
                _add(evidence, str(snippet))
            if label:
                if score is not None:
                    formatted = f"{label} ({_format_score(score)})"
                    if score >= _HIGH_SCORE:
                        _add(strengths, formatted)
                    elif score <= _LOW_SCORE:
                        _add(gaps, formatted)
                    elif category == "strengths":
                        _add(strengths, formatted)
                    elif category == "gaps":
                        _add(gaps, formatted)
                else:
                    if category == "strengths":
                        _add(strengths, label)
                    elif category == "gaps":
                        _add(gaps, label)
            for subkey, subval in value.items():
                if subkey in {"label", "name", "term", "score", "value", "confidence", "weight", "match"}:
                    continue
                if subkey in snippet_keys:
                    continue
                scalar = _coerce_scalar(subval) if subkey in {"met", "present"} else None
                if scalar is not None:
                    continue
                _process(subkey, subval, hint=category)
            return

        if isinstance(value, str):
            target = evidence if category not in {"strengths", "gaps"} else strengths if category == "strengths" else gaps
            _add(target, value)
            return

        if isinstance(value, bool):
            label = _humanize(key or "")
            if not label:
                return
            if value:
                _add(strengths, label)
            else:
                _add(gaps, f"Missing {label}")
            return

        if isinstance(value, (int, float)):
            label = _humanize(key or "")
            formatted = _format_score(float(value))
            if label:
                if value >= _HIGH_SCORE:
                    _add(strengths, f"{label} ({formatted})")
                elif value <= _LOW_SCORE:
                    _add(gaps, f"{label} ({formatted})")
                elif category == "strengths":
                    _add(strengths, f"{label} ({formatted})")
                elif category == "gaps":
                    _add(gaps, f"{label} ({formatted})")
                else:
                    _add(evidence, f"{label}: {formatted}")
            else:
                if category == "strengths":
                    _add(strengths, formatted)
                elif category == "gaps":
                    _add(gaps, formatted)
                else:
                    _add(evidence, formatted)
            return

        if isinstance(value, (list, tuple, set)):
            for item in value:
                _process(key, item, hint=category)
            return

        label = _humanize(key or "")
        text = str(value)
        if category == "strengths":
            _add(strengths, text if not label else f"{label}: {text}")
        elif category == "gaps":
            _add(gaps, text if not label else f"{label}: {text}")
        else:
            _add(evidence, text if not label else f"{label}: {text}")

    for key, value in signals.items():
        _process(key, value)

    strengths_text = "; ".join(strengths) if strengths else "None noted"
    gaps_text = "; ".join(gaps) if gaps else "None noted"
    evidence_text = "; ".join(evidence) if evidence else "None provided"

    return strengths_text, gaps_text, evidence_text

def build_rationale(signals: dict, weights: dict, jd=JD_PD_WEB3, use_llm=False) -> str:
    strengths, gaps, evidence = _summarize_signals(signals)
    ctx = {
        "jd": jd,
        "strengths": strengths,
        "gaps": gaps,
        "evidence": evidence,
        "weights": weights,
    }
    rationale = _render_rationale(ctx)
    if use_llm:
        rationale = _soften_rationale(rationale)
    return rationale


@lru_cache(maxsize=1)
def _rationale_template() -> Template:
    template_path = Path(__file__).with_name("templates") / "rationale_pd.jinja2"
    with template_path.open("r", encoding="utf-8") as template_file:
        return Template(template_file.read())


def _render_rationale(context: dict[str, Any]) -> str:
    return _rationale_template().render(**context)


def _soften_rationale(text: str) -> str:
    prompt = (
        "You revise hiring rationale summaries. "
        "Keep the Markdown structure and factual content identical, "
        "but smooth any sharp language with encouraging, professional phrasing. "
        "Return Markdown only.\n\nRationale to soften:\n"
        f"{text.strip()}\n"
    )
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": LLM_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0},
            },
            timeout=8,
        )
        response.raise_for_status()
        softened = response.json().get("response", "").strip()
        return softened or text
    except Exception:
        return text
