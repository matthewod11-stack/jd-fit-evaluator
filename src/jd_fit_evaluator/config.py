from __future__ import annotations
import pathlib
from pydantic import BaseModel, Field, DirectoryPath, field_validator
from pydantic_settings import BaseSettings

class EmbeddingConfig(BaseModel):
    provider: str = Field(default="openai", pattern="^(openai|ollama|mock)$")
    model: str = "text-embedding-3-small"
    batch_size: int = Field(default=256, ge=1, le=1024)
    timeout_s: int = Field(default=60, ge=5, le=300)

class AppConfig(BaseSettings):
    env: str = Field(default="dev")
    out_dir: DirectoryPath = Field(default_factory=lambda: pathlib.Path("out"))
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")
    greenhouse_deprecated: bool = True
    embeddings: EmbeddingConfig = EmbeddingConfig()

    @field_validator("out_dir")
    @classmethod
    def ensure_out_dir(cls, v: DirectoryPath) -> DirectoryPath:
        pathlib.Path(v).mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        env_prefix = "JD_FIT_"
        case_sensitive = False

cfg = AppConfig()