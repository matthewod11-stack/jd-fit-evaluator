#!/usr/bin/env python3
"""
Create unified ETL tests to ensure all modules work together correctly.
This replaces scattered tests with comprehensive validation.
"""
import sys
import pytest
from pathlib import Path
import tempfile
import csv
import json

# Use proper package imports - no sys.path manipulation needed

def test_manifest_schema_coerce_row():
    """Test coerce_row function with various inputs."""
    from jd_fit_evaluator.etl.manifest_schema import coerce_row, ManifestRow
    
    # Create temporary test file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp.write(b'%PDF-1.4\ntest content')
        test_file_path = tmp.name
    
    try:
        # Test basic coercion
        raw = {
            "candidate_id": "test123",
            "source_path": test_file_path,
            "name": "John Doe",
            "email": "john@example.com"
        }
        result = coerce_row(raw)
        assert isinstance(result, ManifestRow)
        assert result.candidate_id == "test123"
        assert result.name == "John Doe"
        
        # Test legacy field mapping (resume_path -> source_path)
        legacy_raw = {
            "candidate_id": "test456", 
            "resume_path": test_file_path  # Should map to source_path
        }
        result = coerce_row(legacy_raw)
        assert result.candidate_id == "test456"
        # coerce_row returns absolute path, so check the filename
        assert Path(result.source_path).name == Path(test_file_path).name
        
        print("✅ coerce_row function tests passed")
        
    finally:
        Path(test_file_path).unlink(missing_ok=True)

def test_manifest_ingest_integration():
    """Test manifest ingestion end-to-end."""
    from jd_fit_evaluator.etl.manifest_ingest import read_manifest, ingest_manifest_rows
    from jd_fit_evaluator.etl.manifest_schema import Manifest
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test resume file
        test_resume = temp_path / "test_resume.pdf"
        test_resume.write_bytes(b'%PDF-1.4\ntest resume content')
        
        # Create test manifest CSV
        manifest_csv = temp_path / "test_manifest.csv"
        with manifest_csv.open('w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['candidate_id', 'source_path', 'name', 'email'])
            writer.writerow(['cand1', str(test_resume), 'John Doe', 'john@test.com'])
            writer.writerow(['cand2', str(test_resume), 'Jane Smith', 'jane@test.com'])
        
        # Test reading manifest
        manifest = read_manifest(str(manifest_csv))
        assert isinstance(manifest, Manifest)
        assert len(manifest.rows) == 2
        assert manifest.rows[0].candidate_id == 'cand1'
        assert manifest.rows[1].candidate_id == 'cand2'
        
        # Test full ingestion
        out_dir = temp_path / "output"
        result = ingest_manifest_rows(str(manifest_csv), str(out_dir))
        
        assert result['candidates_written'] == 2
        assert Path(result['output_file']).exists()
        assert Path(result['metadata_file']).exists()
        
        # Verify output format
        with open(result['output_file'], 'r') as f:
            candidates = [json.loads(line) for line in f]
            assert len(candidates) == 2
            assert all('candidate_id' in c for c in candidates)
        
        print("✅ Manifest ingestion integration tests passed")

def test_imports_unified():
    """Test that all imports work from unified locations."""
    try:
        from jd_fit_evaluator.etl.manifest_schema import coerce_row, ManifestRow, Manifest
        from jd_fit_evaluator.etl.manifest_ingest import read_manifest, ingest_manifest_rows, ManifestIngestionError
        from jd_fit_evaluator.etl.ingestion import ingest_manifest_rows as alt_ingest
        print("✅ All unified imports successful")
    except ImportError as e:
        print(f"❌ Import failure: {e}")
        raise

def main():
    """Run all unified ETL tests."""
    print("=== Running Unified ETL Tests ===")
    
    try:
        test_imports_unified()
        test_manifest_schema_coerce_row()
        test_manifest_ingest_integration()
        
        print("\n=== All ETL Tests Passed ===")
        return 0
        
    except Exception as e:
        import traceback
        print(f"\n❌ Test failed: {e}")
        print("Full traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())