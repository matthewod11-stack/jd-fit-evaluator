# tests/test_embeddings_batch.py
from jd_fit_evaluator.models.embeddings import embed_texts

def test_mock_batch(tmp_path):
    texts = ["foo","bar"]*100
    out = embed_texts(texts, str(tmp_path/"c.db"))
    assert all(len(v)==1536 for v in out)