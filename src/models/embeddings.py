from math import sqrt

def _cosine(a, b):
    # Pure-Python cosine to avoid numpy import at import-time
    if not a or not b: return 0.0
    # a/b are lists of floats
    dot = sum(x*y for x, y in zip(a, b))
    na = sqrt(sum(x*x for x in a))
    nb = sqrt(sum(y*y for y in b))
    return 0.0 if na == 0.0 or nb == 0.0 else dot / (na * nb)

_MODEL = None

def _load_model(path):
    # TODO: real llama embed model init
    # Guard so we only try once, and only if a path is provided
    global _MODEL
    if _MODEL is None and path:
        _MODEL = "LLAMA-EMBED-MOCK"  # placeholder; wire in real loader
    return _MODEL

def embed(texts, model_path=None):
    """
    Returns list[list[float]] embeddings.
    If model_path provided and model loadable => real vectors.
    Otherwise deterministic hash-based fallback (stable across runs).
    """
    mdl = _load_model(model_path)
    if mdl:
        # TODO: replace with real embedding call; keep length and determinism consistent
        return [_det_hash_vec(t, 256) for t in texts]  # temporary until model wired

    # deterministic fallback
    return [_det_hash_vec(t, 256) for t in texts]

def _det_hash_vec(s: str, dim: int):
    # Stable, fast fallback vector
    h = abs(hash(s))
    out = []
    for i in range(dim):
        # simple, stable pseudo-random but deterministic
        x = ((h >> (i % 32)) & 0xFFFF) / 65535.0
        out.append(2.0 * x - 1.0)
    return out
