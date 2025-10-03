from __future__ import annotations
import pathlib
from pydantic import BaseModel, Field, DirectoryPath, field_validator
from pydantic_settings import BaseSettings

class EmbeddingConfig(BaseModel):
    provider: str = Field(default="mock", pattern="^(openai|ollama|mock)$")
    model: str = "text-embedding-3-small"
    dim: int = Field(default=1536, ge=1, le=4096)
    batch_size: int = Field(default=256, ge=1, le=1024)
    timeout_s: int = Field(default=60, ge=5, le=300)

class LLMConfig(BaseModel):
    provider: str = Field(default="mock", pattern="^(openai|ollama|mock)$")
    model: str = "llama3.1"
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1, le=32000)
    timeout_s: int = Field(default=60, ge=5, le=300)

class AppConfig(BaseSettings):
    env: str = Field(default="dev")
    out_dir: DirectoryPath = Field(default_factory=lambda: pathlib.Path("out"))
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")
    greenhouse_deprecated: bool = True
    embeddings: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)

    def __init__(self, **data):
        # Handle legacy EMBED_* environment variables before initialization
        import os

        # Map EMBED_BACKEND to embeddings.provider (deterministic -> mock)
        if "EMBED_BACKEND" in os.environ:
            backend = os.environ["EMBED_BACKEND"].lower()
            if backend == "deterministic":
                os.environ.setdefault("JD_FIT_EMBEDDINGS__PROVIDER", "mock")
            elif backend in ("openai", "ollama"):
                os.environ.setdefault("JD_FIT_EMBEDDINGS__PROVIDER", backend)

        # Map EMBED_MODEL to embeddings.model
        if "EMBED_MODEL" in os.environ:
            os.environ.setdefault("JD_FIT_EMBEDDINGS__MODEL", os.environ["EMBED_MODEL"])

        # Map EMBED_DIM to embeddings.dim
        if "EMBED_DIM" in os.environ:
            os.environ.setdefault("JD_FIT_EMBEDDINGS__DIM", os.environ["EMBED_DIM"])

        super().__init__(**data)

    @field_validator("out_dir")
    @classmethod
    def ensure_out_dir(cls, v: DirectoryPath) -> DirectoryPath:
        pathlib.Path(v).mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        env_prefix = "JD_FIT_"
        case_sensitive = False

cfg = AppConfig()

# Legacy compatibility exports
LLM_MODEL = cfg.llm.model
USE_LLM_STINTS = True  # Always enable LLM stints processing

# Legacy EMBED_* exports (for archived modules only)
EMBED_BACKEND = cfg.embeddings.provider  # Maps mock -> deterministic for legacy code
EMBED_MODEL = cfg.embeddings.model
EMBED_DIM = cfg.embeddings.dim
EMBED_CACHE_PATH = ".cache/embeddings.db"  # Default cache path

# Legacy settings wrapper for deprecated modules
class LegacySettings:
    def __init__(self, config: AppConfig):
        self._config = config
        # Deprecated Greenhouse settings
        self.gh_token = None
        self.gh_job_id = None
    
    def __getattr__(self, name):
        # Fallback to the main config
        return getattr(self._config, name)

settings = LegacySettings(cfg)