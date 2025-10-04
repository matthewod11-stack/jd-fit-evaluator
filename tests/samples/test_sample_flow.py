import csv
import io
import json
import shlex
import shutil
import subprocess
from pathlib import Path

from jd_fit_evaluator.cli import LEGACY_CSV_HEADERS

ROOT = Path(__file__).resolve().parents[2]  # repo root (adjust if layout differs)
DOCS = ROOT / "docs"
OUT = ROOT / "out"
DATA_OUT = ROOT / "data" / "out"
GOLDENS = ROOT / "tests" / "goldens" / "pd"
JD_PATH = DOCS / "Agoric_Senior_Product_Designer_JD.txt"

SAMPLE_CMD = (
    "python -m jd_fit_evaluator.cli score data/sample --role product-designer --explain -o out"
)

def _run(cmd: str):
    """Utility to run shell commands in tests. Captures output for debugging."""
    return subprocess.run(cmd, shell=True, check=False, cwd=ROOT, capture_output=True, text=True)


def _maybe_get_scores_csv() -> Path | None:
    for candidate in (OUT / "scores.csv", DATA_OUT / "scores.csv"):
        if candidate.exists():
            return candidate
    return None


def _ensure_scores_csv_from_legacy() -> Path:
    """
    PR-06: Prefer canonical out/scores.csv. If only a stale UI export exists under data/out,
    coerce/copy it over so downstream assertions read the right file.
    """
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / "scores.csv"
    if target.exists():
        return target

    legacy_csv = DATA_OUT / "scores.csv"
    if legacy_csv.exists():
        shutil.copyfile(legacy_csv, target)
        return target

    legacy_json = DATA_OUT / "scores.legacy.json"
    if not legacy_json.exists():
        return target

    rows = json.loads(legacy_json.read_text())
    if not isinstance(rows, list):
        return target

    with target.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=LEGACY_CSV_HEADERS)
        writer.writeheader()
        for row in rows:
            payload = {key: row.get(key, "") for key in LEGACY_CSV_HEADERS}
            writer.writerow(payload)
    return target


def _ensure_sample_outputs() -> tuple[Path, Path]:
    scores = _maybe_get_scores_csv()
    rationales = OUT / "rationales.md"
    if scores == DATA_OUT / "scores.csv":
        scores = _ensure_scores_csv_from_legacy()

    needs_refresh = False
    if scores and scores.exists():
        with scores.open(newline="", encoding="utf-8", errors="ignore") as fh:
            reader = csv.DictReader(fh)
            headers = reader.fieldnames or []
            first_row = next(reader, None)
        if set(LEGACY_CSV_HEADERS) - set(headers):
            needs_refresh = True
        elif first_row and not (first_row.get("title_canonical") or first_row.get("industry_canonical")):
            needs_refresh = True

    # Check that both files exist and rationales has content (not just empty file)
    if scores and scores.exists() and rationales.exists() and rationales.stat().st_size > 0 and not needs_refresh:
        return scores, rationales

    result = _run(SAMPLE_CMD)
    assert result.returncode == 0, result.stderr or result.stdout

    scores = _maybe_get_scores_csv()
    if not scores or scores == DATA_OUT / "scores.csv":
        scores = _ensure_scores_csv_from_legacy()
    assert scores.exists(), f"Expected sample scores CSV at {scores}"
    assert rationales.exists(), "Expected out/rationales.md after sample run"
    return scores, rationales


def _canonicalize_csv(text: str) -> str:
    reader = csv.reader(io.StringIO(text.strip()))
    rows = [row for row in reader if row]
    if not rows:
        return ""
    header, *data = rows
    data.sort()
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    for row in data:
        writer.writerow(row)
    return buffer.getvalue().strip()


def _normalize_block(text: str) -> str:
    lines = [line.rstrip() for line in text.strip().splitlines()]
    return "\n".join(lines)


def test_pd_sample_artifacts_exist():
    """
    PR-06: Run the sample flow for the PD role and assert core artifacts exist.
    Uses the existing JD at docs/Agoric_Senior_Product_Designer_JD.txt.
    """
    jd = JD_PATH
    assert jd.exists(), "Missing PD JD at docs/Agoric_Senior_Product_Designer_JD.txt"

    scores_csv, rationales_md = _ensure_sample_outputs()

    assert scores_csv.exists(), "Expected out/scores.csv after sample run (or coerced from data/out)"
    assert rationales_md.exists(), "Expected out/rationales.md after sample run"


def test_pd_sample_mentions_pd_in_outputs():
    """
    PR-06: Heuristic check that PD role language flows through (non-snapshot).
    """
    scores_csv, _ = _ensure_sample_outputs()
    text = scores_csv.read_text(errors="ignore")
    assert "Designer" in text or "Design" in text, "Scores should reflect Product Design role"


def test_pd_sample_matches_goldens():
    """PR-06: Snapshot regression for PD sample outputs."""
    scores_csv, rationales_md = _ensure_sample_outputs()

    actual_csv = _canonicalize_csv(scores_csv.read_text(encoding="utf-8"))
    golden_csv = _canonicalize_csv((GOLDENS / "scores.csv").read_text(encoding="utf-8"))
    assert actual_csv == golden_csv, "Sample scores.csv deviates from golden snapshot"

    actual_rationales = _normalize_block(rationales_md.read_text(encoding="utf-8"))
    golden_rationales = _normalize_block((GOLDENS / "rationales.md").read_text(encoding="utf-8"))
    assert actual_rationales == golden_rationales, "Sample rationales.md deviates from golden snapshot"
