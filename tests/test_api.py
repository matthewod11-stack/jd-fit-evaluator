"""
Tests for jd_fit_evaluator.api module (Pydantic models).
Achieves comprehensive coverage of src/jd_fit_evaluator/api.py
"""
import pytest
from pydantic import ValidationError
from jd_fit_evaluator.api import ScoreRequest, ScoreResponse


class TestScoreRequest:
    """Tests for ScoreRequest Pydantic model."""

    def test_score_request_creation_valid(self):
        """Test creating ScoreRequest with valid data."""
        request = ScoreRequest(
            jd_text="We are hiring a Senior Product Designer with Figma expertise.",
            candidate_text="Alice Smith, 5 years in UX/UI, expert in Figma and prototyping.",
            role="product-designer"
        )

        assert request.jd_text == "We are hiring a Senior Product Designer with Figma expertise."
        assert request.candidate_text == "Alice Smith, 5 years in UX/UI, expert in Figma and prototyping."
        assert request.role == "product-designer"

    def test_score_request_validation_missing_fields(self):
        """Test ScoreRequest validation fails with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            ScoreRequest(jd_text="test")  # Missing candidate_text and role

        errors = exc_info.value.errors()
        error_fields = [e['loc'][0] for e in errors]
        assert 'candidate_text' in error_fields
        assert 'role' in error_fields

    def test_score_request_validation_empty_strings(self):
        """Test ScoreRequest accepts empty strings."""
        request = ScoreRequest(
            jd_text="",
            candidate_text="",
            role=""
        )

        assert request.jd_text == ""
        assert request.candidate_text == ""
        assert request.role == ""

    def test_score_request_json_schema_example(self):
        """Test ScoreRequest has proper JSON schema examples."""
        schema = ScoreRequest.model_json_schema()

        assert "examples" in schema
        examples = schema["examples"]
        assert len(examples) > 0

        example = examples[0]
        assert "jd_text" in example
        assert "candidate_text" in example
        assert "role" in example
        assert example["role"] == "product-designer"

    def test_score_request_serialization(self):
        """Test ScoreRequest can be serialized to JSON."""
        request = ScoreRequest(
            jd_text="JD text",
            candidate_text="Candidate text",
            role="engineer"
        )

        json_str = request.model_dump_json()
        assert "JD text" in json_str
        assert "Candidate text" in json_str
        assert "engineer" in json_str

    def test_score_request_deserialization(self):
        """Test ScoreRequest can be deserialized from dict."""
        data = {
            "jd_text": "Looking for designer",
            "candidate_text": "Designer with 3 years exp",
            "role": "designer"
        }

        request = ScoreRequest(**data)
        assert request.jd_text == "Looking for designer"
        assert request.candidate_text == "Designer with 3 years exp"
        assert request.role == "designer"

    def test_score_request_with_long_text(self):
        """Test ScoreRequest handles long text fields."""
        long_text = "A" * 10000

        request = ScoreRequest(
            jd_text=long_text,
            candidate_text=long_text,
            role="test-role"
        )

        assert len(request.jd_text) == 10000
        assert len(request.candidate_text) == 10000

    def test_score_request_with_special_characters(self):
        """Test ScoreRequest handles special characters."""
        request = ScoreRequest(
            jd_text="Looking for Sr. Designer (Web3) — must have Figma/Sketch",
            candidate_text="Designer with €50k salary @ TechCo™",
            role="product-designer"
        )

        assert "—" in request.jd_text
        assert "€" in request.candidate_text
        assert "™" in request.candidate_text


class TestScoreResponse:
    """Tests for ScoreResponse Pydantic model."""

    def test_score_response_creation_valid(self):
        """Test creating ScoreResponse with valid data."""
        response = ScoreResponse(
            candidate_id="alice-smith",
            fit_score=82.5,
            rationale="Candidate has 5 years in UX/UI and strong Figma skills."
        )

        assert response.candidate_id == "alice-smith"
        assert response.fit_score == 82.5
        assert response.rationale == "Candidate has 5 years in UX/UI and strong Figma skills."

    def test_score_response_validation_missing_fields(self):
        """Test ScoreResponse validation fails with missing required fields."""
        with pytest.raises(ValidationError) as exc_info:
            ScoreResponse(candidate_id="test")  # Missing fit_score and rationale

        errors = exc_info.value.errors()
        error_fields = [e['loc'][0] for e in errors]
        assert 'fit_score' in error_fields
        assert 'rationale' in error_fields

    def test_score_response_fit_score_range(self):
        """Test ScoreResponse accepts various fit_score values."""
        # Test minimum score
        response_min = ScoreResponse(
            candidate_id="min",
            fit_score=0.0,
            rationale="No match"
        )
        assert response_min.fit_score == 0.0

        # Test maximum score
        response_max = ScoreResponse(
            candidate_id="max",
            fit_score=100.0,
            rationale="Perfect match"
        )
        assert response_max.fit_score == 100.0

        # Test decimal score
        response_decimal = ScoreResponse(
            candidate_id="decimal",
            fit_score=73.8,
            rationale="Good match"
        )
        assert response_decimal.fit_score == 73.8

    def test_score_response_json_schema_example(self):
        """Test ScoreResponse has proper JSON schema examples."""
        schema = ScoreResponse.model_json_schema()

        assert "examples" in schema
        examples = schema["examples"]
        assert len(examples) > 0

        example = examples[0]
        assert "candidate_id" in example
        assert "fit_score" in example
        assert "rationale" in example
        assert example["candidate_id"] == "alice-smith"
        assert example["fit_score"] == 82.5

    def test_score_response_serialization(self):
        """Test ScoreResponse can be serialized to JSON."""
        response = ScoreResponse(
            candidate_id="john-doe",
            fit_score=90.0,
            rationale="Excellent candidate"
        )

        json_str = response.model_dump_json()
        assert "john-doe" in json_str
        assert "90" in json_str
        assert "Excellent candidate" in json_str

    def test_score_response_deserialization(self):
        """Test ScoreResponse can be deserialized from dict."""
        data = {
            "candidate_id": "jane-smith",
            "fit_score": 75.5,
            "rationale": "Strong technical background"
        }

        response = ScoreResponse(**data)
        assert response.candidate_id == "jane-smith"
        assert response.fit_score == 75.5
        assert response.rationale == "Strong technical background"

    def test_score_response_with_empty_rationale(self):
        """Test ScoreResponse with empty rationale string."""
        response = ScoreResponse(
            candidate_id="test",
            fit_score=50.0,
            rationale=""
        )

        assert response.rationale == ""

    def test_score_response_with_long_rationale(self):
        """Test ScoreResponse handles long rationale text."""
        long_rationale = "Rationale. " * 1000

        response = ScoreResponse(
            candidate_id="test",
            fit_score=80.0,
            rationale=long_rationale
        )

        assert len(response.rationale) > 1000

    def test_score_response_with_special_characters_in_rationale(self):
        """Test ScoreResponse handles special characters in rationale."""
        response = ScoreResponse(
            candidate_id="test-id",
            fit_score=85.0,
            rationale="Candidate has 5+ years @ TechCo™ with €100k+ revenue impact"
        )

        assert "+" in response.rationale
        assert "@" in response.rationale
        assert "€" in response.rationale

    def test_score_response_candidate_id_formats(self):
        """Test ScoreResponse accepts various candidate_id formats."""
        # Hyphenated
        r1 = ScoreResponse(candidate_id="alice-smith", fit_score=80.0, rationale="test")
        assert r1.candidate_id == "alice-smith"

        # Underscored
        r2 = ScoreResponse(candidate_id="john_doe", fit_score=80.0, rationale="test")
        assert r2.candidate_id == "john_doe"

        # UUID-like
        r3 = ScoreResponse(candidate_id="123e4567-e89b-12d3-a456-426614174000", fit_score=80.0, rationale="test")
        assert r3.candidate_id == "123e4567-e89b-12d3-a456-426614174000"

        # Numeric
        r4 = ScoreResponse(candidate_id="12345", fit_score=80.0, rationale="test")
        assert r4.candidate_id == "12345"


class TestModelIntegration:
    """Integration tests for request/response flow."""

    def test_request_response_round_trip(self):
        """Test creating request and response in sequence."""
        # Create request
        request = ScoreRequest(
            jd_text="Hiring senior engineer",
            candidate_text="Engineer with 10 years experience",
            role="engineer"
        )

        # Simulate processing and create response
        response = ScoreResponse(
            candidate_id="eng-001",
            fit_score=88.5,
            rationale=f"Candidate matches {request.role} role requirements"
        )

        assert response.candidate_id == "eng-001"
        assert response.fit_score == 88.5
        assert request.role in response.rationale

    def test_model_dump_preserves_types(self):
        """Test that model_dump preserves correct types."""
        request = ScoreRequest(
            jd_text="test",
            candidate_text="test",
            role="test"
        )

        dumped = request.model_dump()
        assert isinstance(dumped, dict)
        assert isinstance(dumped["jd_text"], str)
        assert isinstance(dumped["candidate_text"], str)
        assert isinstance(dumped["role"], str)

        response = ScoreResponse(
            candidate_id="test",
            fit_score=75.5,
            rationale="test"
        )

        dumped = response.model_dump()
        assert isinstance(dumped, dict)
        assert isinstance(dumped["candidate_id"], str)
        assert isinstance(dumped["fit_score"], (int, float))
        assert isinstance(dumped["rationale"], str)
