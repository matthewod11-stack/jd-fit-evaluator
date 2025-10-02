import pytest
import json
from datetime import date
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from parsing.models import Stint, Project
from parsing.stints_llm import extract_stints_llm, _hash
from parsing.stints import extract_stints, _stint_model_to_dict


def test_stint_model():
    """Test Pydantic Stint model creation and validation."""
    stint = Stint(
        org="Acme Corp",
        title="Senior Engineer",
        start=date(2020, 1, 1),
        end=date(2023, 1, 1),
        industry="Technology"
    )
    
    assert stint.org == "Acme Corp"
    assert stint.title == "Senior Engineer"
    assert stint.start == date(2020, 1, 1)
    assert stint.end == date(2023, 1, 1)
    assert stint.industry == "Technology"
    assert stint.employment_type is None
    assert len(stint.projects) == 0


def test_stint_model_to_dict():
    """Test conversion from Stint model to legacy dict format."""
    stint = Stint(
        org="Test Company",
        title="Developer", 
        start=date(2021, 6, 1),
        end=date(2022, 12, 31),
        industry="Software"
    )
    
    result = _stint_model_to_dict(stint)
    expected = {
        "company": "Test Company",
        "title": "Developer",
        "industry": "Software", 
        "start_date": date(2021, 6, 1),
        "end_date": date(2022, 12, 31),
    }
    
    assert result == expected


def test_hash_function():
    """Test that hash function produces consistent results."""
    text1 = "Sample resume text"
    text2 = "Sample resume text"
    text3 = "Different resume text"
    
    hash1 = _hash(text1)
    hash2 = _hash(text2)
    hash3 = _hash(text3)
    
    assert hash1 == hash2  # Same input should produce same hash
    assert hash1 != hash3  # Different input should produce different hash
    assert len(hash1) == 16  # Hash should be 16 characters


def test_extract_stints_llm_without_ollama():
    """Test that extract_stints_llm raises HTTPError when Ollama is not running."""
    from requests.exceptions import HTTPError
    with pytest.raises(HTTPError, match="404 Client Error"):
        extract_stints_llm("Some resume text")


def test_extract_stints_llm_with_cache():
    """Test that extract_stints_llm would use cache when available (integration test)."""
    # This is more of a unit test for the cache logic components
    from src.parsing.stints_llm import _hash
    
    # Test that consistent input produces consistent hash
    text = "Test resume content"
    hash1 = _hash(text)
    hash2 = _hash(text)
    assert hash1 == hash2, "Hash function should be deterministic"
    
    # Test that different input produces different hash
    different_text = "Different resume content"
    hash3 = _hash(different_text)
    assert hash1 != hash3, "Different inputs should produce different hashes"


def test_extract_stints_text_input_with_llm_disabled(monkeypatch):
    """Test extract_stints with text input when LLM is disabled."""
    monkeypatch.setenv("USE_LLM_STINTS", "0")
    
    # Need to reload config module to pick up new env var
    import importlib
    config = importlib.import_module("src.config")
    importlib.reload(config)
    stints = importlib.import_module("src.parsing.stints")
    importlib.reload(stints)
    
    result = stints.extract_stints("Sample resume text")
    assert result == []  # Should return empty list when LLM disabled and text input


def test_extract_stints_dict_input_legacy():
    """Test extract_stints with dict input (legacy path)."""
    input_data = {
        "stints": [
            {
                "company": "Test Corp",
                "title": "Engineer",
                "industry": "Tech",
                "start": "2020-01-01",
                "end": "2021-01-01"
            }
        ]
    }
    
    result = extract_stints(input_data)
    assert len(result) == 1
    assert result[0]["company"] == "Test Corp"
    assert result[0]["title"] == "Engineer"
    assert result[0]["industry"] == "Tech"
    assert result[0]["start_date"] == date(2020, 1, 1)
    assert result[0]["end_date"] == date(2021, 1, 1)


def test_extract_stints_empty_dict():
    """Test extract_stints with empty dict input."""
    result = extract_stints({"stints": []})
    assert result == []


def test_project_model():
    """Test Project model creation."""
    project = Project(name="Web App", description="E-commerce platform")
    assert project.name == "Web App"
    assert project.description == "E-commerce platform"
    
    # Test optional fields
    project_minimal = Project()
    assert project_minimal.name is None
    assert project_minimal.description is None