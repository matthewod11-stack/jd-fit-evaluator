import json, csv
from pathlib import Path
import subprocess, sys
import pytest

def _write_manifest(tmp: Path, n: int = 50) -> Path:
    """Create a test manifest with n candidates."""
    p = tmp / "candidate_manifest.csv"
    with p.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "name", "source_path", "email", "phone", "notes"])
        for i in range(n):
            resume = tmp / f"r{i}.txt"
            resume.write_text(f"Resume {i}\nName: Test Person {i}\nSkills: Figma, Prototyping", encoding="utf-8")
            w.writerow([
                f"c-{i:03d}", 
                f"Test Person {i}", 
                str(resume), 
                f"test{i}@example.com",
                f"+1-555-{i:03d}-{i:04d}",
                f"Test candidate {i}"
            ])
    return p

def test_end_to_end_manifest(tmp_path, monkeypatch):
    """Test complete E2E flow with manifest ingestion."""
    # Force mock embeddings provider for speed
    monkeypatch.setenv("JD_FIT_EMBEDDINGS__PROVIDER", "mock")
    
    manifest = _write_manifest(tmp_path, n=50)
    ingest_dir = tmp_path / "ingest"
    out_dir = tmp_path / "out"

    # Test manifest ingestion
    r1 = subprocess.run([
        sys.executable, "-m", "jd_fit_evaluator.cli", 
        "ingest-manifest", str(manifest), "-o", str(ingest_dir)
    ], capture_output=True, text=True)
    
    assert r1.returncode == 0, f"Ingest failed: {r1.stderr}"
    assert "Successfully ingested 50 candidates" in r1.stdout

    # First, we need to extract the resume file paths from the ingested data and parse them
    # Read the candidates.jsonl to get resume paths
    candidates_jsonl = ingest_dir / "candidates.jsonl"
    resume_paths = []
    with candidates_jsonl.open() as f:
        for line in f:
            candidate = json.loads(line)
            resume_paths.append(candidate["resume_path"])
    
    # Parse the resumes
    parse_dir = tmp_path / "parsed"
    for resume_path in resume_paths:
        resume_file = Path(resume_path)
        r_parse = subprocess.run([
            sys.executable, "-m", "jd_fit_evaluator.cli",
            "parse", str(resume_file.parent), "-o", str(parse_dir)
        ], capture_output=True, text=True)
        # Note: parse command might process multiple files, so we just run it once
        break
    
    # Test scoring on parsed data
    r2 = subprocess.run([
        sys.executable, "-m", "jd_fit_evaluator.cli", 
        "score", str(parse_dir), "--role", "product", 
        "--explain", "-o", str(out_dir)
    ], capture_output=True, text=True)
    
    assert r2.returncode == 0, f"Scoring failed: {r2.stderr}"

    # Validate outputs
    candidates_jsonl = ingest_dir / "candidates.jsonl"
    metadata_json = ingest_dir / "ingestion_metadata.json"
    csv_path = out_dir / "scores.csv"
    jsonl_path = out_dir / "scores.jsonl"
    
    assert candidates_jsonl.exists()
    assert metadata_json.exists()
    assert csv_path.exists()
    assert jsonl_path.exists()
    
    # Validate candidate data structure
    with candidates_jsonl.open() as f:
        first_candidate = json.loads(f.readline())
        assert "candidate_id" in first_candidate
        assert "metadata" in first_candidate
        assert first_candidate["metadata"]["source_manifest"] is True
    
    # Validate metadata
    with metadata_json.open() as f:
        metadata = json.load(f)
        assert metadata["candidates_processed"] == 50
        assert metadata["schema_version"] == "1.0"

def test_manifest_validation_errors(tmp_path):
    """Test manifest validation catches common errors."""
    # Test empty manifest
    empty_manifest = tmp_path / "empty.csv"
    empty_manifest.write_text("candidate_id,source_path\n")
    
    r = subprocess.run([
        sys.executable, "-m", "jd_fit_evaluator.cli", 
        "ingest-manifest", str(empty_manifest)
    ], capture_output=True, text=True)
    
    assert r.returncode == 1
    assert "no valid rows" in r.stderr

def test_duplicate_candidate_ids(tmp_path):
    """Test detection of duplicate candidate IDs."""
    manifest = tmp_path / "duplicates.csv"
    resume1 = tmp_path / "resume1.txt"
    resume2 = tmp_path / "resume2.txt"
    resume1.write_text("Resume 1")
    resume2.write_text("Resume 2")
    
    with manifest.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "source_path"])
        w.writerow(["duplicate-id", str(resume1)])
        w.writerow(["duplicate-id", str(resume2)])
    
    r = subprocess.run([
        sys.executable, "-m", "jd_fit_evaluator.cli", 
        "ingest-manifest", str(manifest)
    ], capture_output=True, text=True)
    
    assert r.returncode == 1
    assert "Duplicate candidate_ids" in r.stderr