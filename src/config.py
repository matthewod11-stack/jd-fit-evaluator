from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    gh_token: str | None = os.getenv("GH_TOKEN")
    gh_job_id: str | None = os.getenv("GH_JOB_ID")
    embed_model_path: str | None = os.getenv("EMBED_MODEL_PATH")
    embed_ctx: int = int(os.getenv("EMBED_CTX", "4096"))
    embed_backend: str = os.getenv("EMBED_BACKEND", "ollama")
    embed_model: str = os.getenv("EMBED_MODEL", "nomic-embed-text")
    embed_dim: int = int(os.getenv("EMBED_DIM", "768"))
    embed_cache_path: str = os.getenv("EMBED_CACHE_PATH", ".cache/embeddings.db")
    
    # LLM stint extraction settings
    use_llm_stints: bool = bool(int(os.getenv("USE_LLM_STINTS", "1")))
    llm_model: str = os.getenv("LLM_MODEL", "llama3:8b")

    @field_validator("embed_backend")
    @classmethod
    def _validate_embed_backend(cls, value: str) -> str:
        allowed_backends = {"ollama", "deterministic"}
        if value not in allowed_backends:
            raise ValueError(f"EMBED_BACKEND must be one of {sorted(allowed_backends)}")
        return value

    @field_validator("embed_dim")
    @classmethod
    def _validate_embed_dim(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("EMBED_DIM must be positive")
        return value

    @field_validator("embed_cache_path")
    @classmethod
    def _validate_embed_cache_path(cls, value: str) -> str:
        if not value:
            raise ValueError("EMBED_CACHE_PATH must be a non-empty string")
        return value

settings = Settings()

EMBED_BACKEND = settings.embed_backend
EMBED_MODEL = settings.embed_model
EMBED_DIM = settings.embed_dim
EMBED_CACHE_PATH = settings.embed_cache_path

# LLM stint extraction config
USE_LLM_STINTS = settings.use_llm_stints
LLM_MODEL = settings.llm_model
