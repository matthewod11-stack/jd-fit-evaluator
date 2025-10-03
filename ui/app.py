
# PR-004: Streamlit aligns to new keys, sorts by fit desc; optional CSV export fix.

import streamlit as st, json
import sys
from pathlib import Path
from typing import Dict, Any
import csv
import html
# Import constants relative to ui module
from .constants import TABLE_COLUMNS, EXPORT_COLUMNS, SUB_COLUMNS

# Import from installed package 
from src.scoring.finalize import compute_fit

DEFAULT_MIN_SCORE = 35
DEFAULT_PAGE_SIZE = 50


def _candidate_label(source: Dict[str, Any]) -> str:
    """Choose a stable identifier for display, falling back to candidate_id or name_norm."""
    for key in ("candidate", "name", "candidate_id", "name_norm", "id"):
        value = source.get(key)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return "unknown"


def _coerce_score(value: Any) -> float:
    """Convert score-like values to floats, defaulting to 0.0 to avoid blank columns."""
    if value in (None, ""):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _normalize_saved_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten legacy/new saved rows so table/export schemas stay consistent."""
    subs_in = row.get("subs") if isinstance(row.get("subs"), dict) else {}
    subs_out: Dict[str, float] = {}
    for key in SUB_COLUMNS:
        subs_out[key] = _coerce_score(row.get(key, subs_in.get(key))) # pyright: ignore[reportOptionalMemberAccess]

    fit_value = row.get("fit", row.get("fit_score"))
    fit = _coerce_score(fit_value)

    why = row.get("why")
    if isinstance(why, list):
        reasons = why
    elif isinstance(why, str):
        reasons = [why]
    else:
        reasons = []

    normalized = {
        "candidate": _candidate_label(row),
        "fit": fit,
        "why": reasons,
        "subs": subs_out,
    }
    normalized.update(subs_out)

    # Preserve identifiers if present for downstream use/export
    for key in ("candidate_id", "name_norm"):
        if key in row:
            normalized[key] = row[key]

    return normalized


def _load_cached_results() -> list[dict]:
    """Load cached scores.json (new or legacy structure) if available."""
    candidates: list[dict] = []
    for path in (Path("data/out/scores.json"), Path("data/out/scores.legacy.json")):
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text())
        except Exception:
            continue

        if isinstance(payload, dict):
            rows = payload.get("results") or payload.get("scores") or []
        elif isinstance(payload, list):
            rows = payload
        else:
            continue

        if not isinstance(rows, list):
            continue

        normalized = [_normalize_saved_row(r) for r in rows if isinstance(r, dict)]
        if normalized:
            normalized.sort(key=lambda r: r.get("fit") or 0.0, reverse=True)
            candidates = normalized
            break

    return candidates

st.set_page_config(page_title="JD Fit Evaluator", layout="wide")
st.title("JD-anchored Candidate Evaluator")


def _format_result_row(candidate: dict, fit_result: dict) -> dict:
    """Flatten subscores so table/export share the same columns."""
    base: Dict[str, Any] = {
        "candidate": candidate.get("candidate") or candidate.get("name"),
        "name": candidate.get("name"),
        "candidate_id": candidate.get("candidate_id") or candidate.get("id"),
        "name_norm": candidate.get("name_norm"),
        "fit": fit_result.get("fit"),
        "why": fit_result.get("why"),
        "subs": dict(fit_result.get("subs") or {}),
    }

    for key in SUB_COLUMNS:
        if key in fit_result:
            base[key] = fit_result.get(key)

    normalized = _normalize_saved_row(base)
    return normalized


def _pretty_signal_name(name: str) -> str:
    text = str(name or "").replace("_", " ").replace("-", " ").strip()
    if not text:
        return "Signal"
    return " ".join(part.capitalize() if part else "" for part in text.split())


def build_confidence_badges_payload(signals: Any) -> list[dict[str, Any]]:
    badges: list[dict[str, Any]] = []
    if not isinstance(signals, dict):
        return badges

    for key, raw in signals.items():
        if raw in (None, ""):
            continue

        confidence_value = None
        label_hint = None

        if isinstance(raw, dict):
            label_hint = raw.get("label") or raw.get("text") or raw.get("name")
            for candidate_key in ("confidence", "score", "value"):
                candidate_value = raw.get(candidate_key)
                if candidate_value is not None:
                    confidence_value = candidate_value
                    break
            if confidence_value is None:
                continue
        else:
            confidence_value = raw

        try:
            confidence_float = float(confidence_value)
        except (TypeError, ValueError):
            continue

        confidence = max(0.0, min(1.0, confidence_float))
        label_text = label_hint or _pretty_signal_name(key)
        badges.append({
            "name": str(key),
            "confidence": confidence,
            "label": f"{label_text} • {confidence:.2f}",
        })

    badges.sort(key=lambda item: item["confidence"], reverse=True)
    return badges


def _confidence_strength(value: float) -> str:
    if value >= 0.75:
        return "high"
    if value >= 0.5:
        return "medium"
    return "low"


def render_confidence_badges(badges: list[dict[str, Any]]) -> None:
    if not badges:
        return

    if not st.session_state.get("_confidence_badges_css_injected", False):
        st.markdown(
            """
            <style>
                .confidence-badge-row { display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.4rem 0 0.6rem; }
                .confidence-badge { padding: 0.18rem 0.55rem; border-radius: 999px; font-size: 0.85rem; border: 1px solid rgba(13, 110, 253, 0.28); background-color: rgba(13, 110, 253, 0.12); color: #0d6efd; }
                .confidence-badge[data-strength="medium"] { border-color: rgba(255, 193, 7, 0.35); background-color: rgba(255, 193, 7, 0.18); color: #967000; }
                .confidence-badge[data-strength="low"] { border-color: rgba(220, 53, 69, 0.35); background-color: rgba(220, 53, 69, 0.15); color: #b02a37; }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.session_state["_confidence_badges_css_injected"] = True

    parts: list[str] = []
    for badge in badges:
        confidence = float(badge.get("confidence", 0.0) or 0.0)
        label = badge.get("label") or _pretty_signal_name(badge.get("name", ""))
        strength = _confidence_strength(confidence)
        parts.append(
            (
                "<span class='confidence-badge' data-strength='{strength}' title='{title}'>"
                "{label}</span>"
            ).format(
                strength=strength,
                title=html.escape(f"{badge.get('name', '')} • {confidence:.2f}"),
                label=html.escape(label),
            )
        )

    st.markdown(
        "<div class='confidence-badge-row'>{}</div>".format("".join(parts)),
        unsafe_allow_html=True,
    )


def parse_role(jd_text: str) -> dict:
    lines = [l.strip("-• ").strip() for l in jd_text.splitlines() if l.strip()]
    titles = [l.replace("Title:", "").strip() for l in lines if l.lower().startswith("title:")]
    level = next((l.split(":")[1].strip() for l in lines if l.lower().startswith("level:")), "senior")
    industries = [s.strip() for l in lines if l.lower().startswith("industries:") for s in l.split(":")[1].split(",")]
    must = [l for l in lines if l.lower().startswith("must-have:")]
    nice = [l for l in lines if l.lower().startswith("nice-to-have:")]
    skills_blob = "\n".join(must + nice)
    return dict(titles=[t.lower() for t in titles] or ["recruiter"],
                level=level.lower(),
                industries=[i.lower() for i in industries],
                jd_skills_blob=skills_blob,
                min_avg_months=18, min_last_months=12)

DEFAULT_W = {"title":0.20,"industry":0.15,"skills":0.30,"context":0.10,"tenure":0.10,"recency":0.10,"bonus":0.05}

with st.sidebar:
    st.header("Role (JD)")
    jd_default = Path('data/sample/jd.txt').read_text() if Path('data/sample/jd.txt').exists() else ""
    jd_text = st.text_area("Paste JD key bullets (use 'Title:', 'Level:', 'Industries:' lines)", value=jd_default, height=240)
    colJD1, colJD2 = st.columns(2)
    with colJD1:
        if st.button("Load sample JD"):
            jd_text = Path('data/sample/jd.txt').read_text()
    with colJD2:
        profile_name = st.text_input("Profile name", value="default")
    st.divider()

    st.header("Weights")
    w_title   = st.slider("Title",   0.0, 1.0, DEFAULT_W["title"], 0.01)
    w_ind     = st.slider("Industry",0.0, 1.0, DEFAULT_W["industry"], 0.01)
    w_skills  = st.slider("Skills (semantic)",0.0,1.0,DEFAULT_W["skills"], 0.01)
    w_ctx     = st.slider("Context", 0.0, 1.0, DEFAULT_W["context"], 0.01)
    w_ten     = st.slider("Tenure",  0.0, 1.0, DEFAULT_W["tenure"], 0.01)
    w_rec     = st.slider("Recency", 0.0, 1.0, DEFAULT_W["recency"], 0.01)
    w_bonus   = st.slider("Bonus",   0.0, 1.0, DEFAULT_W["bonus"], 0.01)

    total = w_title+w_ind+w_skills+w_ctx+w_ten+w_rec+w_bonus
    if total == 0: total = 1.0
    weights = {
        "title":   w_title/total,
        "industry":w_ind/total,
        "skills":  w_skills/total,
        "context": w_ctx/total,
        "tenure":  w_ten/total,
        "recency": w_rec/total,
        "bonus":   w_bonus/total
    }

    st.caption(f"Normalized (sum=1): {weights}")

    colP1, colP2 = st.columns(2)
    with colP1:
        if st.button("Save profile"):
            out = Path("data/profiles"); out.mkdir(parents=True, exist_ok=True)
            Path(out / f"{profile_name}.json").write_text(json.dumps({"jd": jd_text, "weights": weights}, indent=2))
            st.success(f"Saved profile data/profiles/{profile_name}.json")
    with colP2:
        if st.button("Load profile"):
            fp = Path("data/profiles") / f"{profile_name}.json"
            if fp.exists():
                saved = json.loads(fp.read_text())
                jd_text = saved.get("jd", jd_text)
                weights = saved.get("weights", weights)
                st.info("Profile loaded. (Sliders not auto-updated; weights will apply to scoring.)")
            else:
                st.error("Profile not found")

st.header("Candidate JSON")
cand_default = Path('data/sample/candidate_example.json').read_text() if Path('data/sample/candidate_example.json').exists() else '{"name":"Example","titles_norm":[],"stints":[],"skills_blob":"","relevant_bullets_blob":""}'
cand_text = st.text_area("Paste candidate JSON (or use samples from data/ingest after running `make ingest`)", value=cand_default, height=260)

colRun = st.columns(3)
run = colRun[0].button("Score")
save = colRun[1].button("Save Output")
load_ingested = colRun[2].button("Load first ingested candidate (if exists)")

if 'results' not in st.session_state:
    st.session_state['results'] = _load_cached_results()

if load_ingested:
    files = sorted(Path("data/ingest").glob("*.json"))
    if files:
        cand_text = files[0].read_text()
        st.info(f"Loaded {files[0].name}")
    else:
        st.warning("No ingested candidates found. Run `make ingest`.")

if run:
    try:
        role = parse_role(jd_text)
        candidate = json.loads(cand_text)
        res = compute_fit(candidate, role, weights=weights)
        st.session_state['results'].append(_format_result_row(candidate, res))
        st.session_state['results'].sort(key=lambda r: r.get("fit") or 0.0, reverse=True)
    except Exception as e:
        st.error(f"Error: {e}")

confidence_badges_map: dict[int, list[dict[str, Any]]] = {}
for row in st.session_state['results']:
    signals_payload = row.get("signals") or row.get("subs") or {}
    badges = build_confidence_badges_payload(signals_payload)
    if badges:
        confidence_badges_map[id(row)] = badges

st.subheader("Results")
table_rows = [{key: row.get(key) for key in TABLE_COLUMNS}
              for row in st.session_state['results']]
if table_rows:
    st.table(table_rows)
for r in st.session_state['results']:
    st.markdown(f"### {r['candidate']} — Fit **{r['fit']}**")
    badges = confidence_badges_map.get(id(r))
    if badges:
        render_confidence_badges(badges)
    st.write(r['why'])
    st.json(r['subs'])

if save and st.session_state['results']:
    outdir = Path("data/out"); outdir.mkdir(parents=True, exist_ok=True)
    (outdir/"scores.json").write_text(json.dumps(st.session_state['results'], indent=2))
    with (outdir/"scores.csv").open("w", newline="") as f:
        export_rows = [{key: row.get(key) for key in EXPORT_COLUMNS}
                       for row in st.session_state['results']]
        w = csv.DictWriter(f, fieldnames=list(EXPORT_COLUMNS))
        w.writeheader()
        for row in export_rows:
            w.writerow(row)
    st.success("Saved JSON + CSV.")
