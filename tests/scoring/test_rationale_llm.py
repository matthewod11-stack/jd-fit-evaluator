"""
Tests for rationale LLM module.
Achieves comprehensive coverage of jd_fit_evaluator/scoring/rationale_llm.py
"""
import pytest
from unittest.mock import Mock, patch
from jd_fit_evaluator.scoring.rationale_llm import generate_rationale


@pytest.fixture
def mock_llm():
    """Mock LLM provider for testing."""
    llm = Mock()
    llm.chat_json = Mock()
    return llm


class TestGenerateRationale:
    """Tests for generate_rationale function."""

    def test_generate_rationale_success(self, mock_llm):
        """Test successful rationale generation."""
        # Setup mock LLM response
        mock_response = Mock()
        mock_response.text = "Strong match due to 5 years of relevant experience in product design."
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.rationale_llm.get_llm', return_value=mock_llm):
            rationale = generate_rationale(
                role="Senior Product Designer",
                signals_json='{"title": 0.9, "skills": 0.85}',
                evidence="5 years at TechCo, Figma expert"
            )

        assert rationale == "Strong match due to 5 years of relevant experience in product design."
        mock_llm.chat_json.assert_called_once()

    def test_generate_rationale_strips_whitespace(self, mock_llm):
        """Test that rationale output is stripped of whitespace."""
        mock_response = Mock()
        mock_response.text = "  \n  Good candidate with relevant skills.  \n  "
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.rationale_llm.get_llm', return_value=mock_llm):
            rationale = generate_rationale(
                role="Engineer",
                signals_json='{}',
                evidence="Python expert"
            )

        assert rationale == "Good candidate with relevant skills."
        assert not rationale.startswith(" ")
        assert not rationale.endswith(" ")

    def test_generate_rationale_with_empty_evidence(self, mock_llm):
        """Test rationale generation with empty evidence."""
        mock_response = Mock()
        mock_response.text = "Limited information available."
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.rationale_llm.get_llm', return_value=mock_llm):
            rationale = generate_rationale(
                role="Designer",
                signals_json='{"title": 0.5}',
                evidence=""
            )

        assert rationale == "Limited information available."

    def test_generate_rationale_prompt_contains_inputs(self, mock_llm):
        """Test that LLM prompt contains role, signals, and evidence."""
        mock_response = Mock()
        mock_response.text = "test rationale"
        mock_llm.chat_json.return_value = mock_response

        role = "Data Scientist"
        signals = '{"skills": 0.8}'
        evidence = "Machine learning expertise"

        with patch('jd_fit_evaluator.scoring.rationale_llm.get_llm', return_value=mock_llm):
            generate_rationale(role=role, signals_json=signals, evidence=evidence)

        # Check prompt contains inputs
        call_args = mock_llm.chat_json.call_args[0]
        user_prompt = call_args[1]
        assert role in user_prompt
        assert signals in user_prompt
        assert evidence in user_prompt

    def test_generate_rationale_system_prompt(self, mock_llm):
        """Test that system prompt is for hiring screener rationale."""
        mock_response = Mock()
        mock_response.text = "rationale"
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.rationale_llm.get_llm', return_value=mock_llm):
            generate_rationale(role="PM", signals_json="{}", evidence="test")

        # Check system prompt
        call_args = mock_llm.chat_json.call_args[0]
        system_prompt = call_args[0]
        assert "Hiring screener rationale" in system_prompt

    def test_generate_rationale_llm_exception(self, mock_llm):
        """Test that LLM exceptions propagate correctly."""
        mock_llm.chat_json.side_effect = Exception("LLM timeout")

        with patch('jd_fit_evaluator.scoring.rationale_llm.get_llm', return_value=mock_llm):
            with pytest.raises(Exception, match="LLM timeout"):
                generate_rationale(role="test", signals_json="{}", evidence="test")

    def test_generate_rationale_with_complex_signals(self, mock_llm):
        """Test rationale generation with complex signals JSON."""
        mock_response = Mock()
        mock_response.text = "Comprehensive match analysis."
        mock_llm.chat_json.return_value = mock_response

        complex_signals = '{"title": 0.9, "industry": 0.85, "skills": 0.8, "tenure": 0.7, "recency": 0.95}'

        with patch('jd_fit_evaluator.scoring.rationale_llm.get_llm', return_value=mock_llm):
            rationale = generate_rationale(
                role="Senior Engineer",
                signals_json=complex_signals,
                evidence="10 years experience, multiple projects"
            )

        assert rationale == "Comprehensive match analysis."

    def test_generate_rationale_prompt_requests_citations(self, mock_llm):
        """Test that prompt asks for evidence citations."""
        mock_response = Mock()
        mock_response.text = "test"
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.rationale_llm.get_llm', return_value=mock_llm):
            generate_rationale(role="test", signals_json="{}", evidence="test")

        # Check prompt asks for citations
        call_args = mock_llm.chat_json.call_args[0]
        user_prompt = call_args[1]
        assert "citing evidence" in user_prompt.lower()

    def test_generate_rationale_length_guidance(self, mock_llm):
        """Test that prompt specifies desired length."""
        mock_response = Mock()
        mock_response.text = "test"
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.rationale_llm.get_llm', return_value=mock_llm):
            generate_rationale(role="test", signals_json="{}", evidence="test")

        # Check prompt specifies sentence count
        call_args = mock_llm.chat_json.call_args[0]
        user_prompt = call_args[1]
        assert "3–6 sentences" in user_prompt or "3-6 sentences" in user_prompt

    def test_generate_rationale_empty_text_response(self, mock_llm):
        """Test handling of empty LLM response."""
        mock_response = Mock()
        mock_response.text = "   "
        mock_llm.chat_json.return_value = mock_response

        with patch('jd_fit_evaluator.scoring.rationale_llm.get_llm', return_value=mock_llm):
            rationale = generate_rationale(role="test", signals_json="{}", evidence="test")

        # Should return empty string after stripping
        assert rationale == ""
