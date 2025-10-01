
import streamlit as st, json
from pathlib import Path
from typing import Dict, Any
from ..src.scoring.finalize import compute_fit

st.set_page_config(page_title="JD Fit Evaluator", layout="wide")
st.title("JD-anchored Candidate Evaluator")

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
    st.session_state['results'] = []

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
        st.session_state['results'].append({"candidate": candidate.get("name","unknown"), **res})
    except Exception as e:
        st.error(f"Error: {e}")

st.subheader("Results")
for r in st.session_state['results']:
    st.markdown(f"### {r['candidate']} — Fit **{r['fit']}**")
    st.write(r['why'])
    st.json(r['subs'])

if save and st.session_state['results']:
    out = Path("data/out"); out.mkdir(parents=True, exist_ok=True)
    Path(out/"ui_scores.json").write_text(json.dumps(st.session_state['results'], indent=2))
    st.success(f"Saved to {out/'ui_scores.json'}")
