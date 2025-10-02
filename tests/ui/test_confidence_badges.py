import pytest
import importlib

# Sample signal payload for badges
SAMPLE_SIGNALS = {
    "titles": {"score": 0.72, "confidence": 0.84},
    "industry": {"score": 0.66, "confidence": 0.77},
    "tenure": {"score": 0.55, "confidence": 0.60},
    "skills": {"score": 0.48, "confidence": 0.52},
}

@pytest.mark.skip(reason="PR-05: implement a badge seam in ui.app, then unskip")
def test_build_confidence_badges_payload_shape():
    """
        PR-05: Once a testable seam exists, validate we get a stable, testable payload:
            - list of dicts with keys: name, confidence (0–1), label/text, maybe color/variant.
        TODO(PR-05): Implement 'build_confidence_badges_payload' (or similar) in ui.app,
        return a pure-Python structure (no Streamlit objects), then unskip this test.
    """
    app = pytest.importorskip("ui.app")
    payload = app.build_confidence_badges_payload(SAMPLE_SIGNALS)  # type: ignore[attr-defined]
    assert isinstance(payload, list) and payload, "Expected a non-empty list of badge dicts"
    for b in payload:
        assert "name" in b and "confidence" in b, "Badge dict missing required keys"
        assert 0.0 <= float(b["confidence"]) <= 1.0, "Confidence must be in [0,1]"
        # Optional visual hints
        assert "label" in b or "text" in b

@pytest.mark.skip(reason="PR-05: add pure-function renderer or adapter for Streamlit, then unskip")
def test_render_confidence_badges_does_not_throw(monkeypatch):
    """
    PR-05: Provide a pure function that formats badges and calls Streamlit API internally.
    We only assert it doesn't raise, not visual output.
    TODO(PR-05): introduce 'render_confidence_badges(badges)' seam, then unskip this test.
    """
    spec = importlib.util.find_spec("ui.app") # pyright: ignore[reportAttributeAccessIssue]
    if spec is None:
        pytest.skip("ui.app module not available; adjust module path for confidence badge tests")
    app = importlib.import_module(spec.name)
    badges = [
        {"name": "titles", "confidence": 0.84, "label": "Titles • 0.84"},
        {"name": "industry", "confidence": 0.77, "label": "Industry • 0.77"},
    ]
    app.render_confidence_badges(badges)  # type: ignore[attr-defined]
