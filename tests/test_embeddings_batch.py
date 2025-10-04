# tests/test_embeddings_batch.py
from jd_fit_evaluator.models.embeddings import embed_texts
from jd_fit_evaluator.config import cfg

def test_mock_batch(tmp_path, monkeypatch):
    # Configure mock embedding provider for testing
    monkeypatch.setattr(cfg.embeddings, "provider", "mock")
    monkeypatch.setattr(cfg.embeddings, "dim", 1536)

    texts = ["foo","bar"]*100
    out = embed_texts(texts, str(tmp_path/"c.db"))
    assert all(len(v)==1536 for v in out)