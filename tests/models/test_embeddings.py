import numpy as np
import pytest

from src.models.embeddings import DeterministicFallbackEmbedder, OllamaEmbedder, _cosine


def test_shape_and_dtype_ollama_embedder(monkeypatch, tmp_path):
    dim = 768
    vector = [float(i) for i in range(dim)]

    class _MockResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {"embedding": vector}

    def _mock_post(url, json, timeout):
        return _MockResponse()

    monkeypatch.setattr("src.models.embeddings.requests.post", _mock_post)

    embedder = OllamaEmbedder(
        model="test-model",
        dim=dim,
        cache_path=str(tmp_path / "embeddings.db"),
        timeout=1.0,
    )

    result = embedder.embed_text("hello world")

    assert isinstance(result, np.ndarray)
    assert result.shape == (dim,)
    assert result.dtype == np.float64
    assert np.allclose(result, vector)


def test_deterministic_fallback_stability_across_runs():
    embedder_one = DeterministicFallbackEmbedder(dim=32)
    embedder_two = DeterministicFallbackEmbedder(dim=32)
    text = "Principal Machine Learning Engineer"

    vector_first = embedder_one.embed_text(text)
    vector_second = embedder_one.embed_text(text)
    vector_third = embedder_two.embed_text(text)

    assert np.array_equal(vector_first, vector_second)
    assert np.array_equal(vector_first, vector_third)


def test_cosine_handles_zero_vectors():
    zeros = np.zeros(4, dtype=np.float64)
    ones = np.ones(4, dtype=np.float64)

    assert _cosine(zeros, ones) == 0.0
    assert _cosine(ones, zeros) == 0.0
    assert _cosine(zeros, zeros) == 0.0
