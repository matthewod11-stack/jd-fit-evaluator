"""
PR-08: This test scaffolds a 'skip-with-reason' reporting seam.
We assume an ingestion function that iterates manifest rows and collects:
  - processed: List[ManifestRow]
  - skipped: List[{"row": <raw>, "reason": <str>}]
"""
import pytest

from src.etl.ingestion import ingest_manifest_rows as _fake_ingest

def test_ingestion_reports_skipped_rows(tmp_path):
    """PR-08: Ingestion should collect and report rows that fail validation."""
    # Create dummy resume files for testing
    resumes_dir = tmp_path / "resumes"
    resumes_dir.mkdir()
    (resumes_dir / "good1.pdf").write_bytes(b"%PDF-1.4\n")
    (resumes_dir / "good2.pdf").write_bytes(b"%PDF-1.4\n")

    input_rows = [
        {"candidate_id": "good1", "resume_path": str(resumes_dir / "good1.pdf")},
        {"candidate_id": "bad1"},  # missing resume_path
        {"resume_path": str(resumes_dir / "bad2.pdf")},  # missing candidate_id
        {"candidate_id": "good2", "resume_path": str(resumes_dir / "good2.pdf"), "email": "test@example.com"},
    ]

    processed, skipped = _fake_ingest(input_rows)

    assert len(processed) == 2  # good1, good2
    assert len(skipped) == 2    # bad1, bad2

    # Check that skipped entries have row + reason
    for skip_entry in skipped:
        assert "row" in skip_entry
        assert "reason" in skip_entry
        assert isinstance(skip_entry["reason"], str)

    # Check processed entries are properly structured
    for proc_entry in processed:
        assert "candidate_id" in proc_entry
        assert "source_path" in proc_entry
