import importlib
import math
from pathlib import Path


def test_sample_score_no_exceptions(tmp_path, monkeypatch):
    # Use canonical config instead of legacy EMBED_* env vars
    monkeypatch.setenv("JD_FIT_EMBEDDINGS__PROVIDER", "mock")
    monkeypatch.setenv("JD_FIT_EMBEDDINGS__DIM", "768")

    importlib.invalidate_caches()
    config = importlib.import_module("jd_fit_evaluator.config")
    importlib.reload(config)
    embeddings = importlib.import_module("jd_fit_evaluator.models.embeddings")
    importlib.reload(embeddings)
    finalize = importlib.import_module("jd_fit_evaluator.scoring.finalize")
    importlib.reload(finalize)
    cli = importlib.import_module("jd_fit_evaluator.cli")
    importlib.reload(cli)

    role = cli.load_role_from_jd(Path("data/sample/jd.txt"))
    candidate = cli.load_sample_candidate()
    result = finalize.compute_fit(candidate, role)

    assert result["fit"] >= 0 and math.isfinite(result["fit"])
    assert result["why"], "Expected rationale entries"
    subs = result["subs"]
    expected_keys = {"title", "industry", "skills", "context", "tenure", "recency", "bonus"}
    assert expected_keys.issubset(subs.keys())
    assert all(math.isfinite(float(value)) for value in subs.values())
