"""
PR-07: Centralized pytest configuration for deterministic runs.
- Introduces --llm flag for tests that require live LLM calls.
- Registers markers and seeds RNGs.
- Defaults DRY_RUN=true for tests to encourage offline/deterministic paths.
"""
import os, random
import pytest

try:
    import numpy as _np  # type: ignore
except Exception:
    _np = None

def pytest_addoption(parser):
    parser.addoption(
        "--llm",
        action="store_true",
        default=False,
        help="Run tests that require LLM calls or network access (non-deterministic).",
    )

def pytest_configure(config):
    # Register custom markers used across the suite
    config.addinivalue_line("markers", "LLM_REQUIRED: marks tests that need LLM/network")
    config.addinivalue_line("markers", "SNAPSHOT: snapshot/golden comparison tests")

    # Default to deterministic behavior in tests
    random.seed(0)
    os.environ.setdefault("PYTHONHASHSEED", "0")
    os.environ.setdefault("DRY_RUN", "true")          # Prefer offline/deterministic paths by default
    os.environ.setdefault("USE_LLM_STINTS", "0")      # Avoid live LLM by default in unit tests
    os.environ.setdefault("EMBED_BACKEND", "deterministic")  # Force deterministic embedder
    os.environ.setdefault("EMBED_CACHE_PATH", ".cache/test-embeddings.db")

def pytest_collection_modifyitems(config, items):
    """Skip LLM_REQUIRED tests unless --llm is provided."""
    if config.getoption("--llm"):
        return
    skip_llm = pytest.mark.skip(reason="PR-07: Skipped by default. Use --llm to run LLM-dependent tests.")
    for item in items:
        if any(mark.name == "LLM_REQUIRED" for mark in item.iter_markers()):
            item.add_marker(skip_llm)

@pytest.fixture(autouse=True)
def _stable_rng_seed():
    """Autouse fixture to (re)seed common RNGs per test."""
    random.seed(0)
    if _np is not None:
        _np.random.seed(0)
