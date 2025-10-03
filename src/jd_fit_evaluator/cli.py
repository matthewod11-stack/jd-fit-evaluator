from __future__ import annotations
import json, logging
from pathlib import Path
import typer
from pydantic import ValidationError
from jd_fit_evaluator.logging import init_logging
from jd_fit_evaluator.config import cfg
from jd_fit_evaluator.utils.schema import CanonicalScore, write_scores
from jd_fit_evaluator.utils.errors import UserInputError, ConfigError, SchemaError

app = typer.Typer(no_args_is_help=True, add_completion=False)

@app.callback()
def _root(log_level: str = typer.Option(cfg.log_level, help="Log level")):
    init_logging(log_level)

@app.command()
def score(
    candidates: str = typer.Argument(..., help="Dir, JSONL/JSON, or manifest CSV"),
    role: str = typer.Option(..., "--role", "-r"),
    explain: bool = typer.Option(False, "--explain"),
    out_dir: Path = typer.Option(cfg.out_dir, "--out", "-o"),
    strict: bool = typer.Option(True, help="Fail on invalid inputs"),
):
    log = logging.getLogger(__name__)
    try:
        from scoring.finalize import score_candidates

        # Validate that candidates path exists
        candidates_path = Path(candidates)
        if not candidates_path.exists():
            raise UserInputError(f"Candidates path does not exist: {candidates}")

        # Load parsed candidate JSONs
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
            raise UserInputError(f"No parsed candidates found in {candidates}")

        # Score candidates
        items = score_candidates(parsed, role, explain)
        write_scores(items, out_dir)
        typer.echo(f"Scored {len(parsed)} candidates, wrote to {out_dir}")
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
def pipeline(input_dir: str, role: str = typer.Option(...,"--role","-r"), out_dir: Path = typer.Option(cfg.out_dir,"--out","-o"), use_llm: bool=True, explain: bool=True):
    from jd_fit_evaluator.ingest.rename import batch_rename
    from jd_fit_evaluator.parsing.llm_parser import parse_resume_with_llm
    from scoring.finalize import score_candidates

    batch_rename(input_dir)
    parsed=[]
    for f in Path(input_dir).glob("**/*"):
        if f.suffix.lower() not in {".pdf",".docx",".txt"}: continue
        text=f.read_text(errors="ignore")
        pr=parse_resume_with_llm(text).model_dump()
        parsed.append({"path":str(f),"parsed":pr})

    results=score_candidates(parsed, role=role, explain=explain)
    write_scores(results, out_dir)
    typer.echo(f"Pipeline complete! Renamed, parsed {len(parsed)} candidates, and wrote scores to {out_dir}")

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

if __name__ == "__main__":
    app()