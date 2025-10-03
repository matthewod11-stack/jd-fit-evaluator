from __future__ import annotations

import csv

from jd_fit_evaluator.cli import LEGACY_CSV_HEADERS

from tests.samples.test_sample_flow import _ensure_sample_outputs


def _load_scores_csv():
    scores_csv, _ = _ensure_sample_outputs()
    assert scores_csv.exists(), "scores.csv missing—run sample flow first"
    return scores_csv


def test_scores_csv_has_expected_headers():
    """
    PR-06: Ensure the sample CSV retains the schema expected by the CLI legacy export.
    Guards against silent drift while snapshots are being refreshed.
    """
    scores_csv = _load_scores_csv()
    with scores_csv.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames or []

    missing = set(LEGACY_CSV_HEADERS) - set(headers)
    assert not missing, f"Missing headers in scores.csv: {sorted(missing)}"


def test_scores_csv_mentions_pd_tokens():
    """Non-snapshot heuristic until goldens are locked: check for PD-flavored tokens."""
    scores_csv = _load_scores_csv()
    text = scores_csv.read_text(encoding="utf-8", errors="ignore").lower()
    tokens = ("design", "designer", "product design", "ux")
    assert any(token in text for token in tokens), "PD tokens not found in scores.csv"
