import os, numpy as np, hashlib, warnings
from ..config import settings

# Try to load llama-cpp. Fall back to deterministic pseudo-embeddings for demo.
try:
    from llama_cpp import Llama
    _HAVE_LLAMA = True
except Exception as e:
    _HAVE_LLAMA = False

_llm = None
def _load_model():
    global _llm
    if _llm is not None: return _llm
    if not _HAVE_LLAMA:
        warnings.warn("llama-cpp not available; using deterministic pseudo-embeddings")
        _llm = None
        return None
    model_path = settings.embed_model_path
    if not model_path or not os.path.exists(model_path):
        warnings.warn("Embedding model not found; using deterministic pseudo-embeddings")
        _llm = None
        return None
    _llm = Llama(model_path=model_path, embedding=True, n_ctx=settings.embed_ctx)
    return _llm

def embed(text: str) -> np.ndarray:
    m = _load_model()
    if m is None:
        # Deterministic fallback: hash to vector
        h = hashlib.sha256(text.encode('utf-8', errors='ignore')).digest()
        rng = np.random.default_rng(int.from_bytes(h[:8], 'little'))
        v = rng.normal(size=1024).astype('float32')
        v /= (np.linalg.norm(v) + 1e-9)
        return v
    out = m.create_embedding(input=text)
    v = np.array(out["data"][0]["embedding"], dtype='float32')
    v /= (np.linalg.norm(v) + 1e-9)
    return v

def cos(u, v) -> float:
    return float(np.dot(u, v) / (np.linalg.norm(u)*np.linalg.norm(v) + 1e-9))
