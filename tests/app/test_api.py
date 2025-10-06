"""
Tests for FastAPI application endpoints.
Achieves comprehensive coverage of app/api.py endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from app.api import app, Role, Candidate


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Setup test environment - conftest already sets mock embeddings."""
    # conftest.py already sets JD_FIT_EMBEDDINGS__PROVIDER=mock and DIM=768
    # This fixture just ensures isolation
    pass


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def valid_role():
    """Valid role data for testing."""
    return {
        "titles": ["product designer", "ux designer"],
        "level": "senior",
        "industries": ["fintech", "saas"],
        "jd_skills_blob": "Figma, user research, prototyping, design systems",
        "min_avg_months": 18,
        "min_last_months": 12
    }


@pytest.fixture
def valid_candidate():
    """Valid candidate data for testing."""
    return {
        "name": "Jane Doe",
        "titles_norm": [("product designer", 3)],
        "stints": [
            {
                "company": "TechCo",
                "title": "Senior Product Designer",
                "industry": "fintech",
                "duration_months": 24,
                "start": "2022-01",
                "end": "2024-01"
            }
        ],
        "skills_blob": "Figma, Sketch, user research, prototyping",
        "relevant_bullets_blob": "Led design system redesign. Conducted user research.",
        "bonus_flags": [0.05]
    }


class TestScoreEndpoint:
    """Tests for /score endpoint."""

    def test_score_success(self, client, valid_role, valid_candidate):
        """Test successful scoring with valid data."""
        response = client.post(
            "/score",
            json={"role": valid_role, "candidate": valid_candidate}
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "fit" in data
        assert "subs" in data
        assert "why" in data

        # Check fit score is numeric
        assert isinstance(data["fit"], (int, float))
        assert 0 <= data["fit"] <= 100

        # Check subscores exist
        assert "title" in data["subs"]
        assert "industry" in data["subs"]
        assert "skills" in data["subs"]
        assert "context" in data["subs"]
        assert "tenure" in data["subs"]
        assert "recency" in data["subs"]

    def test_score_minimal_candidate(self, client, valid_role):
        """Test scoring with minimal candidate data."""
        minimal_candidate = {
            "name": "John Doe",
            "titles_norm": [],
            "stints": [],
            "skills_blob": "",
            "relevant_bullets_blob": ""
        }

        response = client.post(
            "/score",
            json={"role": valid_role, "candidate": minimal_candidate}
        )

        assert response.status_code == 200
        data = response.json()
        assert "fit" in data
        # Minimal candidate should have low score
        assert data["fit"] < 50

    def test_score_empty_role_titles(self, client, valid_candidate):
        """Test scoring with empty role titles."""
        role_no_titles = {
            "titles": [],
            "level": "senior",
            "industries": ["tech"],
            "jd_skills_blob": "Python, SQL",
            "min_avg_months": 18,
            "min_last_months": 12
        }

        response = client.post(
            "/score",
            json={"role": role_no_titles, "candidate": valid_candidate}
        )

        assert response.status_code == 200

    def test_score_missing_optional_fields(self, client):
        """Test scoring with minimal required fields."""
        role = {
            "titles": ["engineer"],
            "level": "mid",
            "industries": ["tech"],
            "jd_skills_blob": "coding"
        }

        candidate = {
            "name": "Test User"
        }

        response = client.post(
            "/score",
            json={"role": role, "candidate": candidate}
        )

        assert response.status_code == 200

    def test_score_invalid_role_schema(self, client, valid_candidate):
        """Test scoring with invalid role schema."""
        invalid_role = {
            "titles": "not a list",  # Should be list
            "level": "senior"
        }

        response = client.post(
            "/score",
            json={"role": invalid_role, "candidate": valid_candidate}
        )

        # Should return validation error
        assert response.status_code == 422

    def test_score_invalid_candidate_schema(self, client, valid_role):
        """Test scoring with invalid candidate schema."""
        invalid_candidate = {
            "name": 123,  # Should be string
            "titles_norm": "not a list"
        }

        response = client.post(
            "/score",
            json={"role": valid_role, "candidate": invalid_candidate}
        )

        # Should return validation error
        assert response.status_code == 422

    def test_score_missing_required_fields(self, client):
        """Test scoring with missing required fields."""
        response = client.post(
            "/score",
            json={"role": {"titles": []}}  # Missing candidate
        )

        assert response.status_code == 422

    def test_score_multiple_stints(self, client, valid_role):
        """Test scoring candidate with multiple work stints."""
        candidate = {
            "name": "Multi Experience",
            "titles_norm": [("designer", 3), ("engineer", 2)],
            "stints": [
                {
                    "company": "Company A",
                    "title": "Senior Designer",
                    "industry": "fintech",
                    "duration_months": 36
                },
                {
                    "company": "Company B",
                    "title": "Designer",
                    "industry": "saas",
                    "duration_months": 24
                },
                {
                    "company": "Company C",
                    "title": "Junior Designer",
                    "industry": "fintech",
                    "duration_months": 18
                }
            ],
            "skills_blob": "Figma, design systems",
            "relevant_bullets_blob": "Multiple accomplishments"
        }

        response = client.post(
            "/score",
            json={"role": valid_role, "candidate": candidate}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["fit"] > 0


class TestRoleModel:
    """Tests for Role Pydantic model."""

    def test_role_creation_full(self):
        """Test Role model creation with all fields."""
        role = Role(
            titles=["engineer"],
            level="senior",
            industries=["tech"],
            jd_skills_blob="Python, AWS",
            min_avg_months=24,
            min_last_months=18
        )

        assert role.titles == ["engineer"]
        assert role.level == "senior"
        assert role.min_avg_months == 24

    def test_role_creation_defaults(self):
        """Test Role model uses default values."""
        role = Role(
            titles=["designer"],
            level="mid",
            industries=["startup"],
            jd_skills_blob="Figma"
        )

        # Should use default values
        assert role.min_avg_months == 18
        assert role.min_last_months == 12

    def test_role_model_dump(self):
        """Test Role model serialization."""
        role = Role(
            titles=["pm"],
            level="senior",
            industries=["saas"],
            jd_skills_blob="roadmaps"
        )

        dumped = role.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["titles"] == ["pm"]
        assert "min_avg_months" in dumped


class TestCandidateModel:
    """Tests for Candidate Pydantic model."""

    def test_candidate_creation_full(self):
        """Test Candidate model creation with all fields."""
        candidate = Candidate(
            name="Test User",
            titles_norm=[("engineer", 3)],
            stints=[{"company": "Test Corp"}],
            skills_blob="Python",
            relevant_bullets_blob="Built things",
            bonus_flags=[0.1]
        )

        assert candidate.name == "Test User"
        assert len(candidate.titles_norm) == 1
        assert candidate.bonus_flags == [0.1]

    def test_candidate_creation_minimal(self):
        """Test Candidate model with only required fields."""
        candidate = Candidate(name="Minimal User")

        assert candidate.name == "Minimal User"
        # Should use defaults
        assert candidate.titles_norm == []
        assert candidate.stints == []
        assert candidate.skills_blob == ""
        assert candidate.relevant_bullets_blob == ""
        assert candidate.bonus_flags is None

    def test_candidate_model_dump(self):
        """Test Candidate model serialization."""
        candidate = Candidate(
            name="Test",
            stints=[{"title": "Engineer"}]
        )

        dumped = candidate.model_dump()
        assert isinstance(dumped, dict)
        assert dumped["name"] == "Test"
        assert dumped["stints"] == [{"title": "Engineer"}]


class TestAppConfiguration:
    """Tests for FastAPI app configuration."""

    def test_app_title(self):
        """Test app has correct title."""
        assert app.title == "JD Fit Evaluator API"

    def test_app_routes_registered(self):
        """Test expected routes are registered."""
        routes = [route.path for route in app.routes]
        assert "/score" in routes
