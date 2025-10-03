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
        # NOTE: hook up to your existing loader/scorer here
        # items: list[CanonicalScore] = score_candidates(load_candidates_any(candidates, strict), role, explain)
        # For now, write a tiny sanity artifact so the command is runnable post-merge:
        dummy = CanonicalScore(artifact={"version":"canonical-1"}, results=[])
        write_scores([dummy], out_dir)
        typer.echo(f"Wrote scores to {out_dir}")
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

if __name__ == "__main__":
    app()