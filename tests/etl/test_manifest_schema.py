from typing import Any, Dict
import importlib
from pathlib import Path

import pytest

manifest_schema = importlib.import_module("jd_fit_evaluator.etl.manifest_schema")
module_path = Path(manifest_schema.__file__).resolve()
repo_root = Path(__file__).resolve().parents[2]
if not module_path.is_relative_to(repo_root / "src/jd_fit_evaluator/etl"):
    raise AssertionError(f"Unexpected manifest_schema location: {module_path}")

ManifestRow = manifest_schema.ManifestRow
coerce_row = manifest_schema.coerce_row


def test_minimal_valid_row_coerces(tmp_path):
    """PR-08: Minimal valid input should coerce without errors."""
    # Create a dummy PDF file for validation
    test_pdf = tmp_path / "a.pdf"
    test_pdf.write_bytes(b"%PDF-1.4\n")

    raw = {"candidate_id": "123", "resume_path": str(test_pdf)}
    row = coerce_row(raw)
    assert isinstance(row, ManifestRow)
    assert row.candidate_id == "123"
    assert row.source_path.endswith("a.pdf")


@pytest.mark.parametrize(
    "bad",
    [
        {},  # missing all
        {"candidate_id": "x"},  # missing source_path
        {"source_path": "nonexistent.pdf"},  # missing candidate_id and invalid path
    ],
)
def test_missing_required_fields_raise_or_tag(bad: Dict[str, Any]):
    """
    PR-08: Decide policy—either raise ValueError here or allow coerce_row to surface
    a structured error object for 'skip-with-reason'. Start strict; we can relax later.
    """
    with pytest.raises(ValueError):
        coerce_row(bad)
