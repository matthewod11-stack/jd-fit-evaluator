from jd_fit_evaluator.utils.schema import coerce_to_canonical

def test_legacy_to_canonical():
    legacy = {"candidate_id": "X", "score": 77.5, "explanation": "ok"}
    out = coerce_to_canonical(legacy)
    assert out.results[0].fit_score == 77.5