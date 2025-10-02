import csv
import io
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
OUT_SCORES = ROOT / "out" / "scores.csv"
GOLDEN_SCORES = ROOT / "tests" / "goldens" / "pd" / "scores.csv"


def _canonicalize_csv(path: Path) -> str:
    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return ""
    header, *data = rows
    data.sort()
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(data)
    return buffer.getvalue().strip()


@pytest.mark.SNAPSHOT
def test_out_scores_matches_pd_golden():
    assert OUT_SCORES.exists(), "Missing generated out/scores.csv artifact"
    assert GOLDEN_SCORES.exists(), "Missing golden snapshot tests/goldens/pd/scores.csv"

    actual_csv = _canonicalize_csv(OUT_SCORES)
    golden_csv = _canonicalize_csv(GOLDEN_SCORES)
    assert actual_csv == golden_csv, "out/scores.csv deviates from golden snapshot"
