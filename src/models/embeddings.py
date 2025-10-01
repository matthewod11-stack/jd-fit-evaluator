# JDFit Embeddings: Ollama backend + deterministic fallback
# TODO(PR-001): Implement Embedder factory and two concrete embedders.
#  - get_embedder(config) -> embedder with .embed_text(str)->np.ndarray shape (768,)
#  - OllamaEmbedder: calls /api/embeddings (model from config), chunk + mean-pool
#  - DeterministicFallbackEmbedder: blake2s(seed) -> stable 768-d vector
#  - On-disk cache keyed by (backend|model|text_hash)
#  - Normalize text (lowercase, strip emails/phones, collapse whitespace)
#  - Return zero vector for empty text; raise EmbeddingDimError if mismatch

class EmbeddingDimError(Exception):
    """Raised when an embedding vector does not match EMBED_DIM."""
    pass

def get_embedder(config):
    """
    TODO(PR-001): Return an embedder instance based on EMBED_BACKEND.
    Must guarantee .embed_text returns 1-D float array of length EMBED_DIM (768).
    Fallback to DeterministicFallbackEmbedder if Ollama unavailable or shape invalid.
    """
    raise NotImplementedError("PR-001: get_embedder")

class OllamaEmbedder:
    def __init__(self, model: str, dim: int, cache_path: str):
        self.model = model
        self.dim = dim
        self.cache_path = cache_path
        # TODO(PR-001): init cache (LMDB/SQLite). Pre-create tables if needed.

    def embed_text(self, text: str):
        """
        TODO(PR-001): Normalize -> chunk -> POST /api/embeddings -> mean-pool -> validate shape.
        Return np.ndarray (dim,), float64. Return zeros if text is blank.
        """
        raise NotImplementedError("PR-001: OllamaEmbedder.embed_text")

class DeterministicFallbackEmbedder:
    def __init__(self, dim: int, salt: str = "jdfit-v1"):
        self.dim = dim
        self.salt = salt

    def embed_text(self, text: str):
        """
        TODO(PR-001): Use hashlib.blake2s with fixed salt to seed PRNG,
        expand to self.dim floats, L2-normalize; avoid NaN/Inf.
        """
        raise NotImplementedError("PR-001: DeterministicFallbackEmbedder.embed_text")
