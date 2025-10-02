import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out"

def _run(cmd: str):
    return subprocess.run(cmd, shell=True, cwd=ROOT, check=False, capture_output=True, text=True)

def test_cli_sample_runs_in_dry_run_and_produces_scores_csv():
    """
    PR-07: Minimal end-to-end sanity under DRY_RUN.
    - Ensures CLI sample path executes without live LLM calls.
    - Confirms artifact presence (scores.csv).
    TODO(PR-07): tighten to compare against a small golden once stable.
    """
    os.environ["DRY_RUN"] = "true"
    pd_jd = ROOT / "docs" / "Agoric_Senior_Product_Designer_JD.txt"
    assert pd_jd.exists(), "Missing PD JD at docs/Agoric_Senior_Product_Designer_JD.txt"
    # Call the CLI directly to avoid Makefile quirks in CI environments
    r = _run("python -m src.cli score docs/Agoric_Senior_Product_Designer_JD.txt --sample")
    assert r.returncode == 0
    assert (OUT / "scores.csv").exists(), "Expected out/scores.csv after DRY_RUN sample"
