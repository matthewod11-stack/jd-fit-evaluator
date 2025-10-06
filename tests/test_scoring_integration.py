"""Test that scoring returns flat list without wrapper."""
import pytest
from jd_fit_evaluator.scoring.finalize import score_candidates, get_scoring_metadata
from jd_fit_evaluator.utils.schema import CanonicalResult


@pytest.fixture
def sample_candidates():
    # Minimal parsed candidate dicts
    candidates = []
    for i in range(12):
        candidates.append({
            "candidate_id": f"c-{i:03d}",
            "name": f"Test Person {i}",
            "emails": [],
            "stints": [],
            "skills_blob": "",
            "relevant_bullets_blob": "",
        })
    return candidates


@pytest.fixture
def sample_role_dict():
    return {
        "role": "Senior Product Designer",
        "titles": ["product designer"],
        "level": "senior",
        "industries": [],
        "jd_skills_blob": "",
    }


def test_score_candidates_returns_flat_list(sample_candidates, sample_role_dict):
    """Ensure score_candidates returns List[CanonicalResult], not wrapped."""
    results = score_candidates(sample_candidates, role=sample_role_dict, explain=False)
    
    # Should be a list
    assert isinstance(results, list), "Results should be a list"
    
    # Should contain CanonicalResult objects
    assert all(isinstance(r, CanonicalResult) for r in results), \
        "All results should be CanonicalResult objects"
    
    # Should have same length as input
    assert len(results) == len(sample_candidates), \
        f"Expected {len(sample_candidates)} results, got {len(results)}"
    
    # Should NOT be a CanonicalScore wrapper
    from jd_fit_evaluator.utils.schema import CanonicalScore
    assert not isinstance(results, CanonicalScore), \
        "Results should not be wrapped in CanonicalScore"
    assert not any(isinstance(r, CanonicalScore) for r in results), \
        "Individual results should not be CanonicalScore objects"


def test_get_scoring_metadata():
    """Test metadata helper function."""
    metadata = get_scoring_metadata("Senior Product Designer")
    
    assert metadata["version"] == "canonical-1"
    assert metadata["role"] == "Senior Product Designer"
    assert "timestamp" in metadata


def test_batch_scoring_integration(sample_candidates, sample_role_dict):
    """Test that batch processing works with flat list."""
    batch_size = 5
    batches = [sample_candidates[i:i+batch_size] 
               for i in range(0, len(sample_candidates), batch_size)]
    
    all_results = []
    for batch in batches:
        batch_results = score_candidates(batch, role=sample_role_dict, explain=False)
        all_results.extend(batch_results)  # Should just work now
    
    assert len(all_results) == len(sample_candidates)
