from __future__ import annotations
import sqlite3, threading, json, time, logging
from contextlib import contextmanager
from typing import List, Dict, Sequence, Optional
from tenacity import retry, wait_exponential, stop_after_attempt
from jd_fit_evaluator.config import cfg

log = logging.getLogger(__name__)

# Thread-local connection store
class _ConnLocal(threading.local):
    def __init__(self):
        self.conn = None
    def get(self, path: str) -> sqlite3.Connection:
        if self.conn is None:
            # Create connection per thread to avoid locking issues
            self.conn = sqlite3.connect(
                path, timeout=30, isolation_level=None, check_same_thread=False
            )
            # Initialize WAL mode with retries
            for _ in range(3):
                try:
                    self.conn.execute("PRAGMA journal_mode=WAL;")
                    break
                except sqlite3.OperationalError:
                    time.sleep(0.01)
            self.conn.execute("PRAGMA synchronous=NORMAL;")
            self.conn.execute("PRAGMA cache_size=10000;")
            self.conn.execute("PRAGMA temp_store=memory;")
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS cache(
                    provider TEXT,
                    model TEXT,
                    text TEXT,
                    vector BLOB,
                    PRIMARY KEY(provider, model, text)
                )"""
            )
        return self.conn

_conn_local = _ConnLocal()
_lock = threading.Lock()

@contextmanager
def conn(path: str):
    yield _conn_local.get(path)

def get_cached(path: str, provider: str, model: str, texts: list[str]) -> dict[str, Optional[list[float]]]:
    out: dict[str, Optional[list[float]]] = {t: None for t in texts}
    with conn(path) as c:
        q = f"SELECT text, vector FROM cache WHERE provider=? AND model=? AND text IN ({','.join(['?']*len(texts))})"
        rows = c.execute(q, [provider, model, *texts]).fetchall()
    for t, vec in rows:
        out[t] = json.loads(vec)
    return out

def put_cached(path: str, provider: str, model: str, items: dict[str, list[float]]) -> None:
    with conn(path) as c, _lock:
        c.executemany(
            "REPLACE INTO cache(provider, model, text, vector) VALUES (?,?,?,?)",
            [(provider, model, t, json.dumps(v)) for t, v in items.items()],
        )

class EmbeddingProvider:
    def embed_batch(self, texts: Sequence[str]) -> List[List[float]]:
        raise NotImplementedError

class MockProvider(EmbeddingProvider):
    def embed_batch(self, texts: Sequence[str]) -> List[List[float]]:
        return [[0.0]*1536 for _ in texts]

class OpenAIProvider(EmbeddingProvider):
    def __init__(self, model: str):
        try:
            import openai
        except ImportError:
            raise ImportError("openai package not installed. Install with: pip install openai")
        self.model = model
        self.client = openai.OpenAI()
    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(5))
    def embed_batch(self, texts: Sequence[str]) -> List[List[float]]:
        resp = self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]

class OllamaProvider(EmbeddingProvider):
    def __init__(self, model: str):
        self.model = model
    @retry(wait=wait_exponential(min=1, max=8), stop=stop_after_attempt(5))
    def embed_batch(self, texts: Sequence[str]) -> List[List[float]]:
        import requests
        url = "http://localhost:11434/api/embeddings"
        out = []
        for t in texts:
            r = requests.post(url, json={"model": self.model, "prompt": t}, timeout=cfg.embeddings.timeout_s)
            r.raise_for_status()
            out.append(r.json()["embedding"])
        return out

def get_provider() -> EmbeddingProvider:
    if cfg.embeddings.provider == "mock":
        return MockProvider()
    if cfg.embeddings.provider == "openai":
        return OpenAIProvider(cfg.embeddings.model)
    if cfg.embeddings.provider == "ollama":
        return OllamaProvider(cfg.embeddings.model)
    raise ValueError(f"Unknown embedding provider: {cfg.embeddings.provider}")

def embed_texts(texts: list[str], cache_path: str) -> list[list[float]]:
    provider = get_provider()
    cached = get_cached(cache_path, cfg.embeddings.provider, cfg.embeddings.model, texts)
    to_fetch = [t for t in texts if cached[t] is None]
    vectors: dict[str, list[float]] = {}
    for i in range(0, len(to_fetch), cfg.embeddings.batch_size):
        chunk = to_fetch[i:i+cfg.embeddings.batch_size]
        t0 = time.time()
        vecs = provider.embed_batch(chunk)
        dt = time.time() - t0
        log.info("Embedded %d texts in %.2fs (%.1f/s)", len(chunk), dt, len(chunk)/dt if dt>0 else 0)
        for t, v in zip(chunk, vecs):
            vectors[t] = v
    if vectors:
        put_cached(cache_path, cfg.embeddings.provider, cfg.embeddings.model, vectors)
    result = []
    for t in texts:
        if cached[t] is not None:
            result.append(cached[t])
        else:
            result.append(vectors[t])
    return result