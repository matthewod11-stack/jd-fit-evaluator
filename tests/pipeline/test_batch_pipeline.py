"""
Golden batch pipeline test: End-to-end manifest → parse → score → export test.

This test validates the complete scoring pipeline using 10-20 real candidates from
the local data directory. It serves as a regression protection "golden snapshot"
for MVP validation.

Test Flow:
1. Ingest manifest CSV (tests/fixtures/sample_manifest.csv with 15 candidates)
2. Parse resumes using LLM parser
3. Score candidates against a role profile
4. Export to JSON and CSV in out/
5. Validate all outputs contain numeric fit scores
"""
from __future__ import annotations
import json
import csv
from pathlib import Path
import pytest
import shutil
import importlib

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures"
SAMPLE_MANIFEST = FIXTURES / "sample_manifest.csv"
OUT_DIR = ROOT / "out" / "batch_pipeline_test"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch, tmp_path):
    """Setup test environment with mock embeddings and clean output directory."""
    # Use mock embeddings and LLM for deterministic tests
    monkeypatch.setenv("JD_FIT_EMBEDDINGS__PROVIDER", "mock")
    monkeypatch.setenv("JD_FIT_EMBEDDINGS__DIM", "768")
    monkeypatch.setenv("JD_FIT_LLM__PROVIDER", "mock")

    # Reload modules to pick up new env vars
    importlib.invalidate_caches()
    config = importlib.import_module("jd_fit_evaluator.config")
    importlib.reload(config)
    embeddings = importlib.import_module("jd_fit_evaluator.models.embeddings")
    importlib.reload(embeddings)
    llm = importlib.import_module("jd_fit_evaluator.models.llm")
    importlib.reload(llm)

    # Clean output directory
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    yield

    # No teardown - keep artifacts for inspection


@pytest.mark.GOLDEN
def test_batch_pipeline_end_to_end():
    """
    Golden test: Full pipeline from manifest ingestion to score export.

    Success criteria:
    - ✅ Manifest ingestion succeeds
    - ✅ All 15 candidates parsed successfully
    - ✅ All 15 candidates scored with numeric fit scores
    - ✅ Output JSON and CSV artifacts created
    - ✅ All fit scores are non-null and in valid range [0, 100]
    """
    from jd_fit_evaluator.etl.manifest_ingest import ingest_manifest_rows
    from jd_fit_evaluator.parsing.llm_parser import parse_resume_with_llm
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from scoring.finalize import score_candidates
    from jd_fit_evaluator.utils.schema import write_scores

    # 1. Verify manifest exists
    assert SAMPLE_MANIFEST.exists(), f"Sample manifest not found: {SAMPLE_MANIFEST}"

    # Count expected candidates
    with SAMPLE_MANIFEST.open() as f:
        reader = csv.DictReader(f)
        manifest_rows = list(reader)
        expected_count = len(manifest_rows)

    assert expected_count >= 10, f"Expected at least 10 candidates, got {expected_count}"
    assert expected_count <= 20, f"Expected at most 20 candidates, got {expected_count}"

    # 2. Ingest manifest → normalized candidates.jsonl
    ingest_dir = OUT_DIR / "ingest"
    result = ingest_manifest_rows(str(SAMPLE_MANIFEST), str(ingest_dir))

    assert result["candidates_written"] == expected_count, \
        f"Expected {expected_count} candidates written, got {result['candidates_written']}"

    candidates_jsonl = Path(result["output_file"])
    assert candidates_jsonl.exists(), f"Candidates JSONL not created: {candidates_jsonl}"

    # 3. Parse resumes from manifest paths
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    from parsing.resume import extract_text

    parsed_candidates = []

    for row in manifest_rows:
        resume_path = Path(row["source_path"])
        assert resume_path.exists(), f"Resume file not found: {resume_path}"

        # Extract text from PDF/DOCX
        try:
            with resume_path.open("rb") as f:
                resume_bytes = f.read()
            text = extract_text(resume_path.name, resume_bytes)

            # Parse with LLM
            parsed = parse_resume_with_llm(text)

            # Add candidate_id to parsed data
            parsed_dict = parsed.model_dump()
            parsed_dict["candidate_id"] = row["candidate_id"]

            parsed_candidates.append({
                "path": str(resume_path),
                "parsed": parsed_dict
            })
        except Exception as e:
            pytest.fail(f"Failed to parse {resume_path}: {e}")

    assert len(parsed_candidates) == expected_count, \
        f"Expected {expected_count} parsed candidates, got {len(parsed_candidates)}"

    # 4. Score candidates against role profile
    role = "Senior Product Designer"  # Uses built-in profile

    try:
        scores = score_candidates(parsed_candidates, role=role, explain=True)
    except Exception as e:
        pytest.fail(f"Scoring failed: {e}")

    assert len(scores) > 0, "No score artifacts returned"

    # Verify CanonicalScore structure
    score_artifact = scores[0]
    assert hasattr(score_artifact, "results"), "Score artifact missing 'results'"
    results = score_artifact.results

    assert len(results) == expected_count, \
        f"Expected {expected_count} scored results, got {len(results)}"

    # 5. Write scores to JSONL and CSV
    scores_dir = OUT_DIR / "scores"
    write_scores(scores, scores_dir)

    scores_jsonl = scores_dir / "scores.jsonl"
    scores_csv = scores_dir / "scores.csv"

    assert scores_jsonl.exists(), f"scores.jsonl not created: {scores_jsonl}"
    assert scores_csv.exists(), f"scores.csv not created: {scores_csv}"

    # 6. Validate JSONL output (read all lines and parse as JSONL)
    json_results = []
    with scores_jsonl.open() as f:
        for line in f:
            line_data = json.loads(line)
            # Extract results from the CanonicalScore artifact
            if "results" in line_data:
                json_results.extend(line_data["results"])

    assert len(json_results) == expected_count, \
        f"JSONL contains {len(json_results)} results, expected {expected_count}"

    # 7. Validate all fit scores are numeric and in range
    for result in json_results:
        assert "candidate_id" in result, f"Result missing candidate_id: {result}"
        assert "fit_score" in result, f"Result missing fit_score for {result.get('candidate_id')}"

        fit_score = result["fit_score"]
        assert fit_score is not None, f"Null fit_score for {result['candidate_id']}"
        assert isinstance(fit_score, (int, float)), \
            f"fit_score is not numeric for {result['candidate_id']}: {type(fit_score)}"
        assert 0 <= fit_score <= 100, \
            f"fit_score out of range [0, 100] for {result['candidate_id']}: {fit_score}"

    # 8. Validate CSV output
    with scores_csv.open(newline="", encoding="utf-8") as f:
        csv_reader = csv.DictReader(f)
        csv_rows = list(csv_reader)

    assert len(csv_rows) == expected_count, \
        f"CSV contains {len(csv_rows)} rows, expected {expected_count}"

    # Verify CSV headers
    required_headers = {"candidate_id", "name", "email", "title_canonical",
                       "industry_canonical", "score"}
    actual_headers = set(csv_rows[0].keys()) if csv_rows else set()

    assert required_headers.issubset(actual_headers), \
        f"CSV missing required headers. Expected {required_headers}, got {actual_headers}"

    # Verify all CSV fit scores are numeric
    for row in csv_rows:
        score_str = row.get("score", "")
        assert score_str, f"Empty score for candidate {row.get('candidate_id')}"

        try:
            score_val = float(score_str)
            assert 0 <= score_val <= 100, \
                f"CSV score out of range for {row['candidate_id']}: {score_val}"
        except ValueError:
            pytest.fail(f"CSV score not numeric for {row['candidate_id']}: {score_str}")

    # 9. Summary validation
    print(f"\n✅ Pipeline test PASSED:")
    print(f"   - Ingested {expected_count} candidates from manifest")
    print(f"   - Parsed {len(parsed_candidates)} resumes")
    print(f"   - Scored {len(results)} candidates")
    print(f"   - Generated valid JSONL: {scores_jsonl}")
    print(f"   - Generated valid CSV: {scores_csv}")
    print(f"   - All {expected_count} candidates have numeric fit scores in [0, 100]")


@pytest.mark.GOLDEN
def test_manifest_validation():
    """Test that sample manifest is valid and contains expected candidates."""
    assert SAMPLE_MANIFEST.exists(), f"Sample manifest not found: {SAMPLE_MANIFEST}"

    with SAMPLE_MANIFEST.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Verify headers
    required_headers = {"candidate_id", "source_path"}
    actual_headers = set(reader.fieldnames) if reader.fieldnames else set()
    assert required_headers.issubset(actual_headers), \
        f"Manifest missing required headers. Expected {required_headers}, got {actual_headers}"

    # Verify row count
    assert 10 <= len(rows) <= 20, \
        f"Expected 10-20 candidates in manifest, got {len(rows)}"

    # Verify all resume files exist
    missing_files = []
    for row in rows:
        resume_path = Path(row["source_path"])
        if not resume_path.exists():
            missing_files.append(str(resume_path))

    assert not missing_files, \
        f"Manifest references {len(missing_files)} missing resume files:\n" + \
        "\n".join(missing_files[:5])
