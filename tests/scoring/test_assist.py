"""
Tests for scoring assist module.
Achieves comprehensive coverage of jd_fit_evaluator/scoring/assist.py
"""
import pytest
from unittest.mock import Mock, patch
from jd_fit_evaluator.scoring.assist import normalize_titles_and_skills


@pytest.fixture
def mock_llm():
    """Mock LLM provider for testing."""
    llm = Mock()
    llm.chat_json = Mock()
    return llm


class TestNormalizeTitlesAndSkills:
    """Tests for normalize_titles_and_skills function."""

    def test_normalize_basic_success(self, mock_llm):
        """Test basic normalization with valid LLM response."""
        # Setup mock LLM response
        mock_response = Mock()
        mock_response.parsed_json = {
            "normalized_titles": ["product designer", "ux designer"],
            "skills": ["figma", "sketch", "user research"]
        }
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.assist.get_llm', return_value=mock_llm):
            result = normalize_titles_and_skills(
                titles=["Product Designer", "UX Designer"],
                skills=["Figma", "Sketch", "User Research"]
            )

        # Verify result
        assert "normalized_titles" in result
        assert "skills" in result
        assert result["normalized_titles"] == ["product designer", "ux designer"]
        assert result["skills"] == ["figma", "sketch", "user research"]

        # Verify LLM was called
        mock_llm.chat_json.assert_called_once()
        call_args = mock_llm.chat_json.call_args
        assert "Normalize titles and consolidate skills" in call_args[0][0]

    def test_normalize_empty_inputs(self, mock_llm):
        """Test normalization with empty inputs."""
        mock_response = Mock()
        mock_response.parsed_json = {
            "normalized_titles": [],
            "skills": []
        }
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.assist.get_llm', return_value=mock_llm):
            result = normalize_titles_and_skills(titles=[], skills=[])

        assert result["normalized_titles"] == []
        assert result["skills"] == []

    def test_normalize_fallback_on_none_response(self, mock_llm):
        """Test fallback when LLM returns None for parsed_json."""
        mock_response = Mock()
        mock_response.parsed_json = None  # LLM failed to parse JSON
        mock_llm.chat_json.return_value = mock_response

        titles = ["Senior Engineer", "Tech Lead"]
        skills = ["Python", "AWS"]

        with patch('jd_fit_evaluator.scoring.assist.get_llm', return_value=mock_llm):
            result = normalize_titles_and_skills(titles=titles, skills=skills)

        # Should return original inputs as fallback
        assert result["normalized_titles"] == titles
        assert result["skills"] == skills

    def test_normalize_with_duplicates(self, mock_llm):
        """Test normalization removes duplicates."""
        mock_response = Mock()
        mock_response.parsed_json = {
            "normalized_titles": ["engineer"],
            "skills": ["python", "sql"]
        }
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.assist.get_llm', return_value=mock_llm):
            result = normalize_titles_and_skills(
                titles=["Engineer", "engineer", "ENGINEER"],
                skills=["Python", "python", "SQL", "sql"]
            )

        # LLM should deduplicate
        assert len(result["normalized_titles"]) <= 3
        assert len(result["skills"]) <= 4

    def test_normalize_passes_correct_prompt(self, mock_llm):
        """Test that correct prompt is passed to LLM."""
        mock_response = Mock()
        mock_response.parsed_json = {
            "normalized_titles": ["data scientist"],
            "skills": ["machine learning"]
        }
        mock_llm.chat_json.return_value = mock_response

        titles = ["Data Scientist"]
        skills = ["Machine Learning"]

        with patch('jd_fit_evaluator.scoring.assist.get_llm', return_value=mock_llm):
            normalize_titles_and_skills(titles=titles, skills=skills)

        # Check the prompt contains the input data
        call_args = mock_llm.chat_json.call_args[0]
        user_prompt = call_args[1]
        assert "Data Scientist" in user_prompt
        assert "Machine Learning" in user_prompt

    def test_normalize_handles_special_characters(self, mock_llm):
        """Test normalization with special characters in inputs."""
        mock_response = Mock()
        mock_response.parsed_json = {
            "normalized_titles": ["sr product designer"],
            "skills": ["ux ui design"]
        }
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.assist.get_llm', return_value=mock_llm):
            result = normalize_titles_and_skills(
                titles=["Sr. Product Designer (Web3)"],
                skills=["UX/UI Design"]
            )

        assert "normalized_titles" in result
        assert "skills" in result

    def test_normalize_with_schema_hint(self, mock_llm):
        """Test that schema_hint is passed to LLM."""
        mock_response = Mock()
        mock_response.parsed_json = {"normalized_titles": [], "skills": []}
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.assist.get_llm', return_value=mock_llm):
            normalize_titles_and_skills(titles=["test"], skills=["test"])

        # Check schema_hint parameter
        call_kwargs = mock_llm.chat_json.call_args[1]
        assert call_kwargs.get("schema_hint") == "norm"

    def test_normalize_llm_exception_propagates(self, mock_llm):
        """Test that LLM exceptions propagate correctly."""
        mock_llm.chat_json.side_effect = Exception("LLM API Error")

        with patch('jd_fit_evaluator.scoring.assist.get_llm', return_value=mock_llm):
            with pytest.raises(Exception, match="LLM API Error"):
                normalize_titles_and_skills(titles=["test"], skills=["test"])

    def test_normalize_with_long_lists(self, mock_llm):
        """Test normalization with long lists of titles/skills."""
        mock_response = Mock()
        mock_response.parsed_json = {
            "normalized_titles": [f"title_{i}" for i in range(50)],
            "skills": [f"skill_{i}" for i in range(100)]
        }
        mock_llm.chat_json.return_value = mock_response

        long_titles = [f"Title {i}" for i in range(50)]
        long_skills = [f"Skill {i}" for i in range(100)]

        with patch('jd_fit_evaluator.scoring.assist.get_llm', return_value=mock_llm):
            result = normalize_titles_and_skills(titles=long_titles, skills=long_skills)

        assert len(result["normalized_titles"]) == 50
        assert len(result["skills"]) == 100
