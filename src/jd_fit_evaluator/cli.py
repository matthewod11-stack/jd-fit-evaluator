from __future__ import annotations
import json, logging
from pathlib import Path
import typer
from pydantic import ValidationError
from jd_fit_evaluator.logging import init_logging
from jd_fit_evaluator.config import cfg
from jd_fit_evaluator.utils.schema import CanonicalScore, write_scores
from jd_fit_evaluator.utils.errors import UserInputError, ConfigError, SchemaError

# Legacy compatibility constants
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

app = typer.Typer(no_args_is_help=True, add_completion=False)

# Legacy compatibility functions
def load_sample_candidate() -> dict:
    """Load a sample candidate from data/sample directory for testing."""
    # Check for Web3 designer candidate first, fallback to default
    for candidate_file in ["candidate_designer_web3.parsed.json", "candidate_example.parsed.json"]:
        p = Path(f"data/sample/{candidate_file}")
        if p.exists():
            return json.loads(p.read_text())
    raise FileNotFoundError("No sample candidate files found")

def load_role_from_jd(jd_path: str | Path) -> dict:
    """Parse a job description file and extract role requirements."""
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

@app.callback()
def _root(log_level: str = typer.Option(cfg.log_level, help="Log level")):
    init_logging(log_level)

@app.command()
def score(
    candidates: str = typer.Argument("", help="Dir, JSONL/JSON, or manifest CSV"),
    role: str = typer.Option(..., "--role", "-r"),
    explain: bool = typer.Option(False, "--explain"),
    out_dir: Path = typer.Option(cfg.out_dir, "--out", "-o"),
    strict: bool = typer.Option(True, help="Fail on invalid inputs"),
    sample: bool = typer.Option(False, "--sample", help="Use sample candidate data"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    # Configure logging based on verbose flag
    log_level = logging.DEBUG if verbose else logging.INFO
    init_logging("DEBUG" if verbose else "INFO")
    log = logging.getLogger(__name__)

    try:
        from jd_fit_evaluator.scoring.finalize import score_candidates

        # Handle --sample flag
        if sample:
            candidates_path = Path("data/sample")
            if not candidates_path.exists():
                raise UserInputError("Sample data directory not found: data/sample")
        else:
            if not candidates:
                raise UserInputError("Candidates path is required (or use --sample)")
            # Validate that candidates path exists
            candidates_path = Path(candidates)
            if not candidates_path.exists():
                raise UserInputError(f"Candidates path does not exist: {candidates}")

        # Load parsed candidate JSONs
        typer.echo(f"📂 Loading candidates from {candidates_path}...")
        parsed = []
        if candidates_path.is_dir():
            for f in candidates_path.glob("**/*.parsed.json"):
                with f.open() as fp:
                    parsed.append({"path": str(f), "parsed": json.load(fp)})
        else:
            # Single file
            with candidates_path.open() as fp:
                parsed.append({"path": str(candidates_path), "parsed": json.load(fp)})

        if not parsed:
            raise UserInputError(f"No parsed candidates found in {candidates_path}")

        typer.echo(f"✓ Loaded {len(parsed)} candidates")
        typer.echo(f"🎯 Scoring against role: {role}")
        typer.echo("")

        # Score candidates (with full logging enabled)
        items = score_candidates(parsed, role, explain)

        typer.echo("")
        typer.echo(f"💾 Writing results to {out_dir}...")
        write_scores(items, out_dir)

        # Summary output
        typer.echo("")
        typer.echo("=" * 60)
        typer.echo("✅ BATCH SCORING COMPLETE")
        typer.echo("=" * 60)
        typer.echo(f"Scored: {len(parsed)} candidates")
        typer.echo(f"Output directory: {out_dir}")
        typer.echo(f"  - scores.jsonl")
        typer.echo(f"  - scores.csv")
        if explain:
            typer.echo(f"  - rationales.md")
        typer.echo("=" * 60)

    except (ValidationError, UserInputError, ConfigError, SchemaError) as e:
        log.error("Validation/config error: %s", e)
        raise typer.Exit(1)
    except Exception:
        log.exception("Fatal error")
        raise typer.Exit(1)

@app.command()
def migrate_schema():
    """Read a single JSON doc from STDIN, write canonical JSON to STDOUT."""
    from jd_fit_evaluator.utils.schema_migrate import main as _main
    _main()

@app.command()
def ui():
    """Launch the Streamlit UI (existing app)."""
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "streamlit", "run", "ui/app.py"])

@app.command()
def rename(input_dir: str):
    from jd_fit_evaluator.ingest.rename import batch_rename
    pairs = batch_rename(input_dir)
    typer.echo(f"Renamed {len(pairs)} files")

@app.command()
def parse(input_dir: str, out_dir: Path = typer.Option(cfg.out_dir, "--out","-o"), use_llm: bool = True):
    from jd_fit_evaluator.parsing.llm_parser import parse_resume_with_llm, ParsedResume
    count=0
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in Path(input_dir).glob("**/*"):
        if f.suffix.lower() not in {".pdf",".docx",".txt"}: continue
        text = f.read_text(errors="ignore")
        pr = parse_resume_with_llm(text) if use_llm else ParsedResume()
        (out_dir/f"{f.stem}.parsed.json").write_text(pr.model_dump_json(indent=2))
        count+=1
    typer.echo(f"Parsed {count} resumes to {out_dir}")

@app.command()
def pipeline(
    input_dir: str,
    role: str = typer.Option(..., "--role", "-r"),
    out_dir: Path = typer.Option(cfg.out_dir, "--out", "-o"),
    use_llm: bool = True,
    explain: bool = True,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    # Configure logging based on verbose flag
    init_logging("DEBUG" if verbose else "INFO")
    log = logging.getLogger(__name__)

    from jd_fit_evaluator.ingest.rename import batch_rename
    from jd_fit_evaluator.parsing.llm_parser import parse_resume_with_llm
    from jd_fit_evaluator.scoring.finalize import score_candidates

    typer.echo("🚀 Starting full pipeline...")
    typer.echo("")

    # Step 1: Rename
    typer.echo("📝 Step 1/3: Renaming files...")
    pairs = batch_rename(input_dir)
    typer.echo(f"✓ Renamed {len(pairs)} files")
    typer.echo("")

    # Step 2: Parse
    typer.echo("📄 Step 2/3: Parsing resumes...")
    parsed = []
    resume_files = list(Path(input_dir).glob("**/*"))
    resume_files = [f for f in resume_files if f.suffix.lower() in {".pdf", ".docx", ".txt"}]

    for idx, f in enumerate(resume_files, 1):
        try:
            typer.echo(f"  [{idx}/{len(resume_files)}] Parsing {f.name}...")
            text = f.read_text(errors="ignore")
            pr = parse_resume_with_llm(text).model_dump()
            parsed.append({"path": str(f), "parsed": pr})
        except Exception as e:
            log.error(f"Failed to parse {f.name}: {e}")
            continue

    typer.echo(f"✓ Parsed {len(parsed)}/{len(resume_files)} resumes")
    typer.echo("")

    # Step 3: Score
    typer.echo("🎯 Step 3/3: Scoring candidates...")
    results = score_candidates(parsed, role=role, explain=explain)

    typer.echo("")
    typer.echo(f"💾 Writing results to {out_dir}...")
    write_scores(results, out_dir)

    # Summary output
    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("✅ PIPELINE COMPLETE")
    typer.echo("=" * 60)
    typer.echo(f"Renamed: {len(pairs)} files")
    typer.echo(f"Parsed: {len(parsed)} resumes")
    typer.echo(f"Scored: {len(parsed)} candidates")
    typer.echo(f"Output directory: {out_dir}")
    typer.echo(f"  - scores.jsonl")
    typer.echo(f"  - scores.csv")
    if explain:
        typer.echo(f"  - rationales.md")
    typer.echo("=" * 60)

@app.command()
def ingest_manifest(
    manifest: str = typer.Argument(..., help="Path to candidate_manifest.csv"),
    out_dir: Path = typer.Option(Path("data/ingest"), "--out", "-o", help="Output dir for normalized candidates"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Ingest a CSV manifest into normalized candidates.jsonl for scoring."""
    import logging
    from jd_fit_evaluator.etl.manifest_ingest import ingest_manifest_rows, ManifestIngestionError

    # Configure logging
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    log = logging.getLogger(__name__)

    try:
        result = ingest_manifest_rows(manifest, str(out_dir))
        typer.echo(f"✅ Successfully ingested {result['candidates_written']} candidates")
        typer.echo(f"📄 Output: {result['output_file']}")
        typer.echo(f"📊 Metadata: {result['metadata_file']}")

    except ManifestIngestionError as e:
        typer.echo(f"❌ Manifest ingestion failed: {e}", err=True)
        if verbose:
            log.exception("Detailed error information:")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Unexpected error: {e}", err=True)
        log.exception("Unexpected error during manifest ingestion:")
        raise typer.Exit(1)

@app.command()
def train(
    scores: Path = typer.Option(..., "--scores", help="Path to scores JSON file"),
    labels: Path = typer.Option(..., "--labels", help="Path to labels CSV file"),
    out: Path = typer.Option(..., "--out", help="Output path for trained model"),
):
    """Train a ranking model from scored candidates and labels."""
    from jd_fit_evaluator.training.train import train as train_model
    import pandas as pd

    log = logging.getLogger(__name__)

    try:
        # Check if labels file exists and has data
        if not labels.exists():
            typer.echo("No labels found - skipping training")
            return

        # Check if labels CSV has any labeled rows
        try:
            labels_df = pd.read_csv(labels)
            if labels_df.empty or "label" not in labels_df.columns:
                typer.echo("No labels found - skipping training")
                return

            labels_df = labels_df.dropna(subset=["label"])
            if labels_df.empty:
                typer.echo("No labels found - skipping training")
                return
        except Exception:
            typer.echo("No labels found - skipping training")
            return

        # Run training
        model_path, meta = train_model(
            scores_path=str(scores),
            labels_csv=str(labels),
            out_path=str(out),
        )
        typer.echo(f"✅ Trained model on {meta['n']} samples")
        typer.echo(f"📄 Model saved to: {model_path}")

    except SystemExit as e:
        # Handle SystemExit from train function
        if e.code == 0:
            typer.echo("No labels found - skipping training")
        else:
            raise typer.Exit(e.code)
    except Exception:
        log.exception("Training failed")
        raise typer.Exit(1)

if __name__ == "__main__":
    app()