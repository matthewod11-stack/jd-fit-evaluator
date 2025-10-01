
import json, os, sys, typer, glob
from pathlib import Path
from typing import Optional
from .config import settings
from .scoring.finalize import compute_fit, build_rationale
from .etl.greenhouse import ingest_job

app = typer.Typer(help="JD-anchored candidate evaluator CLI")

def load_sample_candidate() -> dict:
    # Check for Web3 designer candidate first, fallback to default
    for candidate_file in ["candidate_designer_web3.json", "candidate_example.json"]:
        p = Path(f"data/sample/{candidate_file}")
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("No sample candidate files found")

def load_role_from_jd(jd_path: str) -> dict:
    text = Path(jd_path).read_text()
    lines = [l.strip("-• ").strip() for l in text.splitlines() if l.strip()]
    titles = [l.replace("Title:", "").strip() for l in lines if l.lower().startswith("title:")]
    level = next((l.split(":")[1].strip() for l in lines if l.lower().startswith("level:")), "senior")
    industries = [s.strip() for l in lines if l.lower().startswith("industries:") for s in l.split(":")[1].split(",")]
    must = [l for l in lines if l.lower().startswith("must-have:")]
    nice = [l for l in lines if l.lower().startswith("nice-to-have:")]
    skills_blob = "\n".join(must + nice)
    role = dict(
        titles=[t.lower() for t in titles] or ["recruiter"],
        level=level.lower(),
        industries=[i.lower() for i in industries],
        jd_skills_blob=skills_blob,
        min_avg_months=18, min_last_months=12
    )
    return role

@app.command()
def score(jd: str, sample: bool = False):
    role = load_role_from_jd(jd)
    candidates = []
    if sample:
        candidates = [load_sample_candidate()]
    else:
        for fp in glob.glob("data/ingest/*.json"):
            candidates.append(json.loads(Path(fp).read_text()))
    if not candidates:
        typer.echo("No candidates found. Use --sample or run `make ingest`.")
        raise typer.Exit(1)

    out_dir = Path("data/out"); out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for cand in candidates:
        res = compute_fit(cand, role)
        
        # Extract terms for rationale building
        jd_terms = role.get("jd_skills_blob", "").split()
        resume_terms = []
        if "skills" in cand:
            resume_terms.extend(cand["skills"])
        if "stints" in cand:
            for stint in cand["stints"]:
                resume_terms.extend([stint.get("title", ""), stint.get("industry", ""), stint.get("company", "")])
        
        # Build rationale
        rationale = build_rationale(res["subs"], jd_terms, resume_terms)
        
        rows.append({"candidate": cand.get("name", "unknown"), "fit": res["fit"], **res["subs"], "why": res["why"], "rationale": rationale})
        print(f"{cand.get('name','unknown'):25s}  Fit={res['fit']:5.1f}  Why: " + " | ".join(res["why"]))
    Path(out_dir/"scores.json").write_text(json.dumps(rows, indent=2))
    print(f"Saved scores to {out_dir/'scores.json'}")

@app.command()
def ingest(job_id: Optional[str] = None, out_dir: str = "data/ingest"):
    jid = job_id or settings.gh_job_id
    if not (settings.gh_token and jid):
        typer.echo("Error: GH_TOKEN and GH_JOB_ID must be set (either via .env or --job-id).")
        raise typer.Exit(1)
    files = ingest_job(jid, out_dir=out_dir)
    typer.echo(f"Ingested {len(files)} candidates → {out_dir}")

@app.command()
def train(jd: str = "data/sample/jd.txt", labels: str = "data/labels.csv", scores: str = "data/out/scores.json", out: str = "models/trained/model.pkl"):
    # Ensure features exist; if not, run score first (sample or ingested)
    if not Path(scores).exists():
        typer.echo("Features file not found; run `make score` (or score --sample) first to build data/out/scores.json.")
        raise typer.Exit(1)
    from .training.train import train as _train
    out_path, meta = _train(scores, labels, out)
    typer.echo(f"Trained model → {out_path}  (n={meta['n']}, positive rate={meta['pos_rate']:.2f})")

if __name__ == '__main__':
    app()
