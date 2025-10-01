from __future__ import annotations

import hashlib
import logging
import os
import re
import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import requests

from src.config import EMBED_BACKEND, EMBED_CACHE_PATH, EMBED_DIM, EMBED_MODEL


_OLLAMA_ENDPOINT = os.getenv("OLLAMA_EMBED_URL", "http://localhost:11434/api/embeddings")
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(r"\b(?:\+?\d[\d\s\-()]{6,}\d)\b")
_WHITESPACE_RE = re.compile(r"\s+")


class EmbeddingDimError(Exception):
    """Raised when an embedding vector does not match EMBED_DIM."""


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    lowered = text.lower()
    lowered = _EMAIL_RE.sub(" ", lowered)
    lowered = _PHONE_RE.sub(" ", lowered)
    collapsed = _WHITESPACE_RE.sub(" ", lowered).strip()
    return collapsed


def _chunk_text(text: str, max_chars: int = 1024) -> list[str]:
    if not text:
        return []
    tokens = text.split()
    if not tokens:
        return []
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for token in tokens:
        token_len = len(token)
        projected = current_len + token_len + (1 if current else 0)
        if current and projected > max_chars:
            chunks.append(" ".join(current))
            current = [token]
            current_len = token_len
        else:
            if current:
                current_len += 1  # account for space
            current.append(token)
            current_len += token_len
    if current:
        chunks.append(" ".join(current))
    return chunks


def _hash_text(*parts: str) -> str:
    hasher = hashlib.blake2s(digest_size=32)
    for part in parts:
        hasher.update(part.encode("utf-8"))
        hasher.update(b"|")
    return hasher.hexdigest()


def _ensure_dimension(vector: Iterable[float], dim: int) -> np.ndarray:
    array = np.asarray(vector, dtype=np.float64)
    if array.ndim != 1 or array.shape[0] != dim:
        raise EmbeddingDimError(f"Expected dimension {dim}, received shape {array.shape}")
    return array


def _cosine(a: Iterable[float], b: Iterable[float]) -> float:
    a_arr = np.asarray(a, dtype=np.float64)
    b_arr = np.asarray(b, dtype=np.float64)

    if a_arr.ndim != 1:
        raise ValueError(f"expected 1D vector for 'a', got shape {a_arr.shape}")
    if b_arr.ndim != 1:
        raise ValueError(f"expected 1D vector for 'b', got shape {b_arr.shape}")
    if a_arr.shape[0] != b_arr.shape[0]:
        raise ValueError(
            f"cosine requires matching shapes, got {a_arr.shape[0]} and {b_arr.shape[0]} elements"
        )

    if not (np.isfinite(a_arr).all() and np.isfinite(b_arr).all()):
        raise ValueError("cosine received non-finite values")

    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    value = float(np.dot(a_arr, b_arr) / (norm_a * norm_b))
    if value > 1.0:
        return 1.0
    if value < -1.0:
        return -1.0
    return value


class _EmbeddingCache:
    def __init__(self, path: str):
        self._path = Path(path)
        self._lock = threading.Lock()
        self._conn = self._init_db()

    def _init_db(self) -> sqlite3.Connection:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                cache_key TEXT PRIMARY KEY,
                dim INTEGER NOT NULL,
                vector BLOB NOT NULL
            )
            """
        )
        conn.commit()
        return conn

    def get(self, key: str, dim: int) -> np.ndarray | None:
        with self._lock:
            cursor = self._conn.execute(
                "SELECT vector, dim FROM embeddings WHERE cache_key = ?", (key,)
            )
            row = cursor.fetchone()
        if not row:
            return None
        blob, stored_dim = row
        if stored_dim != dim:
            return None
        vector = np.frombuffer(blob, dtype=np.float64)
        if vector.shape[0] != dim:
            raise EmbeddingDimError(
                f"Cache entry has mismatch dimension: expected {dim}, got {vector.shape[0]}"
            )
        return np.array(vector, copy=True)

    def set(self, key: str, vector: np.ndarray) -> None:
        payload = np.asarray(vector, dtype=np.float64)
        blob = payload.tobytes()
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO embeddings(cache_key, dim, vector) VALUES (?, ?, ?)",
                (key, payload.shape[0], blob),
            )
            self._conn.commit()


class DeterministicFallbackEmbedder:
    def __init__(self, dim: int, salt: str = "jdfit-v1"):
        self.dim = dim
        self.salt = salt

    def embed_text(self, text: str) -> np.ndarray:
        normalized = _normalize_text(text)
        if not normalized:
            return np.zeros(self.dim, dtype=np.float64)
        hasher = hashlib.blake2s(digest_size=32)
        hasher.update(self.salt.encode("utf-8"))
        hasher.update(b"|")
        hasher.update(normalized.encode("utf-8"))
        seed = int.from_bytes(hasher.digest(), "big", signed=False)
        rng = np.random.default_rng(seed)
        vector = rng.standard_normal(self.dim)
        norm = np.linalg.norm(vector)
        if not np.isfinite(norm) or norm == 0.0:
            return np.zeros(self.dim, dtype=np.float64)
        return (vector / norm).astype(np.float64)


class OllamaEmbedder:
    def __init__(self, model: str, dim: int, cache_path: str, timeout: float = 30.0):
        self.model = model
        self.dim = dim
        self.timeout = timeout
        self._cache = _EmbeddingCache(cache_path)

    def _cache_key(self, normalized_text: str) -> str:
        return _hash_text("ollama", self.model, normalized_text)

    def _fetch_embedding(self, chunk: str) -> np.ndarray:
        response = requests.post(
            _OLLAMA_ENDPOINT,
            json={"model": self.model, "prompt": chunk},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload: Any = response.json()
        embedding = payload.get("embedding")
        if embedding is None and isinstance(payload.get("data"), list):
            data = payload["data"]
            if data and isinstance(data[0], dict):
                embedding = data[0].get("embedding")
        if embedding is None:
            raise RuntimeError("Ollama returned no embedding data")
        return _ensure_dimension(embedding, self.dim)

    def embed_text(self, text: str) -> np.ndarray:
        normalized = _normalize_text(text)
        if not normalized:
            return np.zeros(self.dim, dtype=np.float64)
        key = self._cache_key(normalized)
        cached = self._cache.get(key, self.dim)
        if cached is not None:
            return cached

        chunks = _chunk_text(normalized)
        if not chunks:
            chunks = [normalized]

        vectors: list[np.ndarray] = []
        for chunk in chunks:
            vector = self._fetch_embedding(chunk)
            vectors.append(vector)

        if not vectors:
            result = np.zeros(self.dim, dtype=np.float64)
        else:
            matrix = np.vstack(vectors)
            result = _ensure_dimension(matrix.mean(axis=0), self.dim)

        self._cache.set(key, result)
        return result


class _ResilientEmbedder:
    def __init__(self, primary: OllamaEmbedder, fallback: DeterministicFallbackEmbedder):
        self._primary = primary
        self._fallback = fallback

    def embed_text(self, text: str) -> np.ndarray:
        try:
            return self._primary.embed_text(text)
        except (EmbeddingDimError, requests.RequestException, ValueError, RuntimeError) as exc:
            logging.warning("Falling back to deterministic embeddings: %s", exc)
            return self._fallback.embed_text(text)


def _config_value(config: Any, name: str, default: Any) -> Any:
    if config is None:
        return default
    if isinstance(config, dict):
        return config.get(name, default)
    return getattr(config, name, default)


def get_embedder(config: Any = None):
    backend = str(_config_value(config, "EMBED_BACKEND", EMBED_BACKEND)).lower()
    model = _config_value(config, "EMBED_MODEL", EMBED_MODEL)
    dim = int(_config_value(config, "EMBED_DIM", EMBED_DIM))
    cache_path = _config_value(config, "EMBED_CACHE_PATH", EMBED_CACHE_PATH)

    fallback = DeterministicFallbackEmbedder(dim=dim)

    if backend == "deterministic":
        return fallback

    if backend == "ollama":
        primary = OllamaEmbedder(model=model, dim=dim, cache_path=cache_path)
        return _ResilientEmbedder(primary, fallback)

    logging.warning("Unknown embedding backend '%s'; using deterministic fallback", backend)
    return fallback
