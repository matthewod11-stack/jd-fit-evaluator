# tests/test_embeddings_concurrent.py
import threading
from jd_fit_evaluator.models.embeddings import embed_texts

def test_concurrent(tmp_path):
    texts = [f"word-{i}" for i in range(100)]
    cache = tmp_path / "cache.db"
    results = []
    
    def worker():
        out = embed_texts(texts, str(cache))
        results.append(out)
    
    threads = [threading.Thread(target=worker) for _ in range(8)]
    for th in threads: 
        th.start()
    for th in threads: 
        th.join()
    
    assert all(len(r)==len(texts) for r in results)

def test_concurrent_cache(tmp_path):
    texts = [f"word-{i}" for i in range(50)]
    cache = tmp_path / "cache.db"
    results = []
    def worker():
        out = embed_texts(texts, str(cache))
        results.append(out)
    threads = [threading.Thread(target=worker) for _ in range(4)]
    for th in threads: th.start()
    for th in threads: th.join()
    assert all(len(r)==len(texts) for r in results)