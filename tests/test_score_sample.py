import importlib
import math
from pathlib import Path


def test_sample_score_no_exceptions(tmp_path, monkeypatch):
    monkeypatch.setenv("EMBED_BACKEND", "deterministic")
    monkeypatch.setenv("EMBED_CACHE_PATH", str(tmp_path / "embeddings.db"))

    importlib.invalidate_caches()
    config = importlib.import_module("src.config")
    importlib.reload(config)
    embeddings = importlib.import_module("src.models.embeddings")
    importlib.reload(embeddings)
    finalize = importlib.import_module("src.scoring.finalize")
    importlib.reload(finalize)
    cli = importlib.import_module("src.cli")
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
