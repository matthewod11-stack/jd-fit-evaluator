from __future__ import annotations

import csv
import re
from datetime import datetime, timezone
from pathlib import Path
import json
import glob
from typing import Optional
import typer

ARTIFACT_VERSION = "scores.v2"

LEGACY_CSV_HEADERS = [
    "candidate_id",
    "name",
    "email",
    "title_canonical",
    "industry_canonical",
    "score",
    "titles_score",
    "industry_score",
    "tenure_score",
    "skills_score",
    "context_score",
]


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return normalized.strip("-")


def _infer_jd_label(jd_path: str) -> str:
    candidate = Path(jd_path).stem or Path(jd_path).name
    slug = _slugify(candidate)
    return slug or "jd"


def _make_artifact_header(jd_path: str, *, candidate_count: int) -> dict:
    embed_cfg = {
        "backend": settings.embed_backend,
        "model": settings.embed_model,
        "dim": settings.embed_dim,
        "ctx": settings.embed_ctx,
    }
    if settings.embed_model_path:
        embed_cfg["model_path"] = settings.embed_model_path
    if settings.embed_cache_path:
        embed_cfg["cache_path"] = settings.embed_cache_path

    return {
        "version": ARTIFACT_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "jd_label": _infer_jd_label(jd_path),
        "source_jd": str(Path(jd_path)),
        "candidate_count": candidate_count,
        "embed_config": embed_cfg,
    }


def _first_non_empty_string(*candidates) -> str:
    for candidate in candidates:
        if candidate is None:
            continue
        if isinstance(candidate, str):
            value = candidate.strip()
            if value:
                return value
        elif isinstance(candidate, dict):
            for key in ("value", "label", "text", "name"):
                if key in candidate:
                    nested = _first_non_empty_string(candidate[key])
                    if nested:
                        return nested
        elif isinstance(candidate, (list, tuple)):
            for item in candidate:
                nested = _first_non_empty_string(item)
                if nested:
                    return nested
    return ""


def _name_norm(candidate: dict) -> str:
    raw = candidate.get("name") or candidate.get("candidate") or ""
    slug = _slugify(raw)
    if slug:
        return slug
    cid = candidate.get("candidate_id") or candidate.get("id")
    return _slugify(str(cid)) if cid else ""

from .config import settings
from .scoring.finalize import compute_fit, build_rationale
from .etl.greenhouse import ingest_job

# Typer app (avoid Annotated to sidestep Typer/Click parsing edge cases)
app = typer.Typer(help="JD-anchored candidate evaluator CLI", rich_markup_mode=None)

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
def score(
    jd: str = typer.Argument(..., help="Path to job description file"),
    sample: bool = typer.Option(False, "--sample", is_flag=True, help="Use sample candidate data"),
):
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

    out_dir = Path("data/out")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    legacy_rows = []
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
        subs = res["subs"]
        display_name = cand.get("name", "unknown")
        candidate_id = cand.get("candidate_id") or cand.get("id")

        enriched_row = {
            "candidate_id": candidate_id,
            "candidate": display_name,
            "name": display_name,
            "name_norm": _name_norm(cand),
            "fit": res["fit"],
            "why": res["why"],
            "rationale": rationale,
            "subs": subs,
        }
        enriched_row.update(subs)
        rows.append(enriched_row)

        # Build a compact legacy-friendly row that matches LEGACY_CSV_HEADERS.
        # helper to safely extract a score value that may be a float or a dict
        def _score_of(key: str):
            v = subs.get(key)
            if isinstance(v, dict):
                return v.get("score", "")
            if v is None:
                return ""
            return v

        title_canonical = _first_non_empty_string(
            subs.get("title"),
            subs.get("title_norm"),
            cand.get("title"),
            [stint.get("title") for stint in cand.get("stints", [])],
        )
        industry_canonical = _first_non_empty_string(
            subs.get("industry"),
            subs.get("industry_norm"),
            cand.get("industry"),
            [stint.get("industry") for stint in cand.get("stints", [])],
        )

        legacy_row = {
            "candidate_id": candidate_id if candidate_id is not None else "",
            "name": display_name,
            "email": cand.get("email", ""),
            # canonical fields - prefer explicit keys in `subs`, fall back to candidate metadata
            "title_canonical": title_canonical,
            "industry_canonical": industry_canonical,
            "score": res.get("fit", ""),
            # signal-level numeric scores (expected floats) — try plural key then singular
            "titles_score": _score_of("titles") or _score_of("title"),
            "industry_score": _score_of("industry"),
            "tenure_score": _score_of("tenure"),
            "skills_score": _score_of("skills"),
            "context_score": _score_of("context"),
        }
        legacy_rows.append(legacy_row)

        print(f"{display_name:25s}  Fit={res['fit']:5.1f}  Why: " + " | ".join(res["why"]))

    artifact = _make_artifact_header(jd, candidate_count=len(rows))
    payload = {"artifact": artifact, "results": rows}

    scores_path = out_dir/"scores.json"
    legacy_path = out_dir/"scores.legacy.json"
    scores_path.write_text(json.dumps(payload, indent=2))
    legacy_path.write_text(json.dumps(legacy_rows, indent=2))
    print(f"Saved scores to {scores_path} (legacy list: {legacy_path})")

    # Maintain legacy CSV artifact in repo-root `out/` for snapshot tests.
    legacy_csv_root = Path("out")
    legacy_csv_root.mkdir(parents=True, exist_ok=True)
    legacy_csv_path = legacy_csv_root / "scores.csv"
    with legacy_csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEGACY_CSV_HEADERS)
        writer.writeheader()
        for row in legacy_rows:
            payload_row = {}
            for key in LEGACY_CSV_HEADERS:
                value = row.get(key)
                payload_row[key] = "" if value is None else value
            writer.writerow(payload_row)
    print(f"Saved legacy CSV to {legacy_csv_path}")

    # Also write a consolidated rationale file expected by some acceptance scripts
    # (legacy acceptance checks look for `out/rationales.md`). We write into
    # repository-root `out/` to keep that expectation stable.
    rationales_path = legacy_csv_root / "rationales.md"
    with rationales_path.open("w", encoding="utf-8") as rf:
        for r in rows:
            # Each `rationale` may be a string or a list of lines/blocks. Normalize
            # to a Markdown string before writing.
            raw = r.get("rationale", "")
            if isinstance(raw, (list, tuple)):
                rationale_text = "\n\n".join(str(x).strip() for x in raw if x is not None)
            else:
                rationale_text = str(raw)
            rf.write(rationale_text.rstrip() + "\n\n")
    print(f"Saved rationales to {rationales_path}")

@app.command()
def ingest(
    job_id: Optional[str] = typer.Option(None, "--job-id", help="Greenhouse job ID"),
    out_dir: str = typer.Option("data/ingest", "--out-dir", help="Output directory for ingested data"),
):
    jid = job_id or settings.gh_job_id
    if not (settings.gh_token and jid):
        typer.echo("Error: GH_TOKEN and GH_JOB_ID must be set (either via .env or --job-id).")
        raise typer.Exit(1)
    files = ingest_job(jid, out_dir=out_dir)
    typer.echo(f"Ingested {len(files)} candidates → {out_dir}")

def train_impl(
    jd: str = "data/sample/jd.txt",
    labels: str = "data/labels.csv", 
    scores: str = "data/out/scores.json",
    out: str = "models/trained/model.pkl"
):
    """Implementation function that can be called directly or from CLI."""
    # Ensure features exist; if not, run score first (sample or ingested)
    if not Path(scores).exists():
        print("Features file not found; run `make score` (or score --sample) first to build data/out/scores.json.")
        raise SystemExit(1)
    labels_path = Path(labels)
    if not labels_path.exists() or labels_path.stat().st_size == 0:
        print("No labels found; skipping training.")
        raise SystemExit(0)
    from .training.train import train as _train
    out_path, meta = _train(scores, labels, out)
    print(f"Trained model → {out_path}  (n={meta['n']}, positive rate={meta['pos_rate']:.2f})")
    return out_path, meta

@app.command()
def train(
    jd: str = typer.Option("data/sample/jd.txt", "--jd", help="Path to job description file"),
    labels: str = typer.Option("data/labels.csv", "--labels", help="Path to labels CSV file"),
    scores: str = typer.Option("data/out/scores.json", "--scores", help="Path to scores JSON file"),
    out: str = typer.Option("models/trained/model.pkl", "--out", help="Output path for trained model"),
):
    """CLI command wrapper for train_impl."""
    return train_impl(jd, labels, scores, out)

def main():
    app()

if __name__ == "__main__":
    main()
