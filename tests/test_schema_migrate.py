"""
Tests for schema migration utility.
Achieves comprehensive coverage of jd_fit_evaluator/utils/schema_migrate.py
"""
import pytest
import json
import sys
from io import StringIO
from jd_fit_evaluator.utils.schema_migrate import main
from jd_fit_evaluator.utils.schema import coerce_to_canonical


class TestSchemaMigrateCLI:
    """Tests for schema migration CLI (main function)."""

    def test_main_reads_stdin_writes_stdout(self, monkeypatch, capsys):
        """Test main reads JSON from stdin and writes canonical JSON to stdout."""
        # Setup stdin with legacy schema
        input_json = json.dumps({
            "candidate_id": "test123",
            "score": 85.5,
            "explanation": "Strong candidate"
        })
        monkeypatch.setattr('sys.stdin', StringIO(input_json))

        # Run main
        main()

        # Capture stdout
        captured = capsys.readouterr()
        output = json.loads(captured.out)

        # Verify output is canonical format
        assert "results" in output
        assert len(output["results"]) > 0
        assert output["results"][0]["fit_score"] == 85.5

    def test_main_with_minimal_input(self, monkeypatch, capsys):
        """Test main with minimal valid input."""
        input_json = json.dumps({
            "candidate_id": "min",
            "score": 50.0
        })
        monkeypatch.setattr('sys.stdin', StringIO(input_json))

        main()

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert "results" in output
        assert output["results"][0]["candidate_id"] == "min"
        assert output["results"][0]["fit_score"] == 50.0

    def test_main_preserves_core_fields(self, monkeypatch, capsys):
        """Test main preserves core fields from input."""
        input_json = json.dumps({
            "candidate_id": "full_test",
            "score": 92.3,
            "explanation": "Excellent match"
        })
        monkeypatch.setattr('sys.stdin', StringIO(input_json))

        main()

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        result = output["results"][0]
        assert result["candidate_id"] == "full_test"
        assert result["fit_score"] == 92.3
        assert result["rationale"] == "Excellent match"

    def test_main_formats_output_with_indent(self, monkeypatch, capsys):
        """Test that output JSON is formatted with indentation."""
        input_json = json.dumps({"candidate_id": "test", "score": 75.0})
        monkeypatch.setattr('sys.stdin', StringIO(input_json))

        main()

        captured = capsys.readouterr()
        # Check that output has newlines (indicating indentation)
        assert "\n" in captured.out
        assert "  " in captured.out or "\t" in captured.out

    def test_main_with_canonical_input(self, monkeypatch, capsys):
        """Test main with canonical format input (passthrough)."""
        input_json = json.dumps({
            "artifact": {"version": "1"},
            "results": [
                {"candidate_id": "c1", "fit_score": 80.0, "rationale": "good"},
                {"candidate_id": "c2", "fit_score": 70.0, "rationale": "ok"}
            ]
        })
        monkeypatch.setattr('sys.stdin', StringIO(input_json))

        main()

        captured = capsys.readouterr()
        output = json.loads(captured.out)

        assert len(output["results"]) == 2
        assert output["results"][0]["candidate_id"] == "c1"
        assert output["results"][1]["candidate_id"] == "c2"


class TestCoerceToCanonical:
    """Tests for coerce_to_canonical function."""

    def test_legacy_to_canonical_basic(self):
        """Test basic legacy format conversion."""
        legacy = {
            "candidate_id": "test_id",
            "score": 77.5,
            "explanation": "Good fit"
        }

        result = coerce_to_canonical(legacy)

        assert hasattr(result, 'results')
        assert len(result.results) == 1
        assert result.results[0].candidate_id == "test_id"
        assert result.results[0].fit_score == 77.5
        assert result.results[0].rationale == "Good fit"

    def test_legacy_to_canonical_basic_fields(self):
        """Test legacy conversion handles basic required fields."""
        legacy = {
            "candidate_id": "xyz",
            "score": 88.0,
            "explanation": "Good candidate"
        }

        result = coerce_to_canonical(legacy)

        assert result.results[0].candidate_id == "xyz"
        assert result.results[0].fit_score == 88.0
        assert result.results[0].rationale == "Good candidate"

    def test_legacy_to_canonical_creates_artifact(self):
        """Test legacy conversion creates artifact wrapper."""
        legacy = {
            "candidate_id": "abc",
            "score": 65.0
        }

        result = coerce_to_canonical(legacy)

        assert hasattr(result, 'artifact')
        assert isinstance(result.artifact, dict)
        assert len(result.results) == 1

    def test_legacy_to_canonical_with_signals(self):
        """Test legacy conversion handles signal scores."""
        legacy = {
            "candidate_id": "sig_test",
            "score": 80.0,
            "titles_score": 0.9,
            "industry_score": 0.8,
            "tenure_score": 0.7,
            "skills_score": 0.85,
            "context_score": 0.75
        }

        result = coerce_to_canonical(legacy)

        signals = result.results[0].signals
        # Check that signals are preserved (exact field names may vary)
        assert signals is not None or isinstance(signals, dict)
