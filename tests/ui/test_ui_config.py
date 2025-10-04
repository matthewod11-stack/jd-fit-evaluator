import importlib
import importlib.util
import types


def _load_ui_app_module() -> types.ModuleType:
    """Locate the UI app module regardless of package layout."""
    for module_name in ("ui.app", "src.ui.app", "app.ui"):
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            continue
        return importlib.import_module(spec.name)
    raise AssertionError("Unable to locate the UI app module; tried ui.app, src.ui.app, app.ui")

def test_threshold_defaults_exist_and_are_relaxed():
    """
    PR-05: Ensure default gating is more permissive for discovery.
    """
    app = _load_ui_app_module()
    # Must exist
    assert hasattr(app, "DEFAULT_MIN_SCORE"), "DEFAULT_MIN_SCORE missing"
    assert hasattr(app, "DEFAULT_PAGE_SIZE"), "DEFAULT_PAGE_SIZE missing"
    # Should reflect relaxed defaults introduced by PR-05
    # NOTE: If you finalized different values, update the assertions accordingly.
    assert app.DEFAULT_MIN_SCORE <= 45, "DEFAULT_MIN_SCORE should be relaxed (<=45)"
    assert app.DEFAULT_PAGE_SIZE >= 25, "DEFAULT_PAGE_SIZE should be >=25 for broader visibility"


def test_confidence_badges_seam_is_present_or_skipped():
    """
    PR-05: Prefer a testable seam for the UI 'confidence badges'.
    We don't assert Streamlit rendering here; we only check that a seam function exists.
    """
    app = _load_ui_app_module()
    assert hasattr(app, "render_confidence_badges") or hasattr(app, "build_confidence_badges_payload"), (
        "Missing a testable badges seam (render_confidence_badges/build_confidence_badges_payload). "
        "Add a helper function and update tests."
    )
