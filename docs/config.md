# JD-Fit Evaluator Configuration Reference

This document provides comprehensive configuration guidance for the JD-Fit Evaluator system.

## Table of Contents

- [Overview](#overview)
- [Configuration Methods](#configuration-methods)
- [Environment Variables](#environment-variables)
- [Provider Configuration](#provider-configuration)
- [Advanced Configuration](#advanced-configuration)
- [Configuration Examples](#configuration-examples)
- [Troubleshooting](#troubleshooting)

## Overview

JD-Fit Evaluator uses **Pydantic Settings** for configuration management with hierarchical loading:

1. **Default values** (defined in [src/jd_fit_evaluator/config.py](../src/jd_fit_evaluator/config.py))
2. **Environment variables** (`.env` file or shell exports)
3. **Runtime overrides** (command-line arguments where applicable)

All configuration uses the `JD_FIT_` prefix to avoid conflicts with other tools.

## Configuration Methods

### Method 1: `.env` File (Recommended)

Create a `.env` file in the project root:

```bash
# .env
JD_FIT_ENV=dev
JD_FIT_LOG_LEVEL=INFO
JD_FIT_EMBEDDINGS__PROVIDER=ollama
JD_FIT_EMBEDDINGS__MODEL=llama3.1
```

The `.env` file is automatically loaded by `python-dotenv` and ignored by git (see [.gitignore](../.gitignore)).

### Method 2: Shell Environment Variables

Export variables in your shell or CI/CD environment:

```bash
export JD_FIT_ENV=prod
export JD_FIT_LOG_LEVEL=WARNING
export JD_FIT_EMBEDDINGS__PROVIDER=openai
export JD_FIT_EMBEDDINGS__MODEL=text-embedding-3-small
```

### Method 3: Programmatic Configuration

Override configuration in Python code:

```python
from jd_fit_evaluator.config import AppConfig, EmbeddingConfig

config = AppConfig(
    env="prod",
    log_level="INFO",
    embeddings=EmbeddingConfig(
        provider="openai",
        model="text-embedding-3-small"
    )
)
```

## Environment Variables

### Core Configuration

| Variable | Description | Default | Valid Values |
|----------|-------------|---------|--------------|
| `JD_FIT_ENV` | Deployment environment | `dev` | `dev`, `prod` |
| `JD_FIT_OUT_DIR` | Output directory for artifacts | `out` | Any valid directory path |
| `JD_FIT_LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Embedding Configuration

| Variable | Description | Default | Valid Values |
|----------|-------------|---------|--------------|
| `JD_FIT_EMBEDDINGS__PROVIDER` | Embedding provider | `mock` | `openai`, `ollama`, `mock` |
| `JD_FIT_EMBEDDINGS__MODEL` | Model name | `text-embedding-3-small` | Provider-specific model ID |
| `JD_FIT_EMBEDDINGS__DIM` | Embedding dimensions | `1536` | Integer: 1-4096 |
| `JD_FIT_EMBEDDINGS__BATCH_SIZE` | Batch processing size | `256` | Integer: 1-1024 |
| `JD_FIT_EMBEDDINGS__TIMEOUT_S` | Request timeout (seconds) | `60` | Integer: 5-300 |

### LLM Configuration

| Variable | Description | Default | Valid Values |
|----------|-------------|---------|--------------|
| `JD_FIT_LLM__PROVIDER` | LLM provider | `mock` | `openai`, `ollama`, `mock` |
| `JD_FIT_LLM__MODEL` | Model name | `llama3.1` | Provider-specific model ID |
| `JD_FIT_LLM__TEMPERATURE` | Sampling temperature | `0.1` | Float: 0.0-2.0 |
| `JD_FIT_LLM__MAX_TOKENS` | Max generation tokens | `4096` | Integer: 1-32000 |
| `JD_FIT_LLM__TIMEOUT_S` | Request timeout (seconds) | `60` | Integer: 5-300 |

### Legacy Environment Variables

For backwards compatibility, the following legacy variables are supported:

| Legacy Variable | New Variable | Notes |
|----------------|--------------|-------|
| `EMBED_BACKEND` | `JD_FIT_EMBEDDINGS__PROVIDER` | `deterministic` maps to `mock` |
| `EMBED_MODEL` | `JD_FIT_EMBEDDINGS__MODEL` | Direct mapping |
| `EMBED_DIM` | `JD_FIT_EMBEDDINGS__DIM` | Direct mapping |

## Provider Configuration

### OpenAI Provider

OpenAI provides high-quality embeddings and LLM capabilities via API.

**Prerequisites:**
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

**Configuration:**

```bash
# .env
JD_FIT_EMBEDDINGS__PROVIDER=openai
JD_FIT_EMBEDDINGS__MODEL=text-embedding-3-small
JD_FIT_EMBEDDINGS__DIM=1536
JD_FIT_EMBEDDINGS__BATCH_SIZE=256

JD_FIT_LLM__PROVIDER=openai
JD_FIT_LLM__MODEL=gpt-4o-mini
JD_FIT_LLM__TEMPERATURE=0.1

# Required: OpenAI API key
OPENAI_API_KEY=sk-your-api-key-here
```

**Recommended Models:**
- Embeddings: `text-embedding-3-small` (1536 dims, fast, cost-effective)
- Embeddings: `text-embedding-3-large` (3072 dims, higher accuracy)
- LLM: `gpt-4o-mini` (fast, cost-effective)
- LLM: `gpt-4o` (highest quality)

**Cost Considerations:**
- Embedding: ~$0.02 per 1M tokens
- LLM (gpt-4o-mini): ~$0.15 per 1M input tokens
- Monitor usage via OpenAI dashboard

### Ollama Provider (Local)

Ollama enables local LLM inference without external API calls.

**Prerequisites:**
- Ollama installed ([installation guide](https://ollama.ai))
- Downloaded models

**Setup:**

```bash
# Install Ollama (macOS/Linux)
curl https://ollama.ai/install.sh | sh

# Pull models
ollama pull llama3.1
ollama pull nomic-embed-text

# Verify installation
ollama list
```

**Configuration:**

```bash
# .env
JD_FIT_EMBEDDINGS__PROVIDER=ollama
JD_FIT_EMBEDDINGS__MODEL=nomic-embed-text
JD_FIT_EMBEDDINGS__DIM=768

JD_FIT_LLM__PROVIDER=ollama
JD_FIT_LLM__MODEL=llama3.1
JD_FIT_LLM__TEMPERATURE=0.1

# Optional: Custom Ollama host
OLLAMA_HOST=http://localhost:11434
```

**Recommended Models:**
- Embeddings: `nomic-embed-text` (768 dims, fast)
- Embeddings: `llama3.1` (4096 dims, slower but more capable)
- LLM: `llama3.1` (8B or 70B variants)
- LLM: `llama3.1:70b` (higher quality, requires more RAM)

**Performance Notes:**
- 8B models: ~8GB RAM, suitable for most use cases
- 70B models: ~40GB RAM, production-quality results
- GPU acceleration recommended for batch processing

### Mock Provider (Testing/Development)

Mock providers use deterministic fallbacks for testing without external dependencies.

**Configuration:**

```bash
# .env
JD_FIT_EMBEDDINGS__PROVIDER=mock
JD_FIT_LLM__PROVIDER=mock
```

**Behavior:**
- **Embeddings**: Generates deterministic vectors based on text hash
- **LLM**: Returns placeholder responses
- **Performance**: Instant, no network calls
- **Use Case**: Testing, CI/CD, development without API keys

**Limitations:**
- Not suitable for production
- Semantic similarity is simulated, not real
- Rationales are generic placeholders

## Advanced Configuration

### Custom Output Directory

Organize outputs by batch or date:

```bash
# Date-based output
JD_FIT_OUT_DIR=out/$(date +%Y-%m-%d)

# Batch-based output
JD_FIT_OUT_DIR=out/batch_01
```

### Production Configuration

Recommended settings for production deployments:

```bash
# .env.production
JD_FIT_ENV=prod
JD_FIT_LOG_LEVEL=WARNING
JD_FIT_OUT_DIR=/var/lib/jd-fit/out

# OpenAI with rate limiting
JD_FIT_EMBEDDINGS__PROVIDER=openai
JD_FIT_EMBEDDINGS__MODEL=text-embedding-3-small
JD_FIT_EMBEDDINGS__BATCH_SIZE=128
JD_FIT_EMBEDDINGS__TIMEOUT_S=120

JD_FIT_LLM__PROVIDER=openai
JD_FIT_LLM__MODEL=gpt-4o-mini
JD_FIT_LLM__TEMPERATURE=0.1
JD_FIT_LLM__MAX_TOKENS=2048
JD_FIT_LLM__TIMEOUT_S=120

OPENAI_API_KEY=${OPENAI_API_KEY_SECRET}
```

### Development Configuration

Settings for local development with fast iteration:

```bash
# .env.development
JD_FIT_ENV=dev
JD_FIT_LOG_LEVEL=DEBUG
JD_FIT_OUT_DIR=out

# Mock providers for speed
JD_FIT_EMBEDDINGS__PROVIDER=mock
JD_FIT_LLM__PROVIDER=mock
```

### Hybrid Configuration

Use different providers for embeddings and LLM:

```bash
# Fast embeddings, high-quality LLM
JD_FIT_EMBEDDINGS__PROVIDER=ollama
JD_FIT_EMBEDDINGS__MODEL=nomic-embed-text

JD_FIT_LLM__PROVIDER=openai
JD_FIT_LLM__MODEL=gpt-4o
```

## Configuration Examples

### Example 1: Quick Start (No Setup)

```bash
# .env (or no .env file)
JD_FIT_EMBEDDINGS__PROVIDER=mock
JD_FIT_LLM__PROVIDER=mock
```

**Use Case:** First-time users, testing, CI/CD
**Command:** `python -m jd_fit_evaluator.cli score --sample --role "Product Designer"`

### Example 2: Local Development (Ollama)

```bash
# .env
JD_FIT_ENV=dev
JD_FIT_LOG_LEVEL=DEBUG

JD_FIT_EMBEDDINGS__PROVIDER=ollama
JD_FIT_EMBEDDINGS__MODEL=nomic-embed-text
JD_FIT_EMBEDDINGS__DIM=768

JD_FIT_LLM__PROVIDER=ollama
JD_FIT_LLM__MODEL=llama3.1
```

**Prerequisites:** Ollama installed with models pulled
**Use Case:** Privacy-focused, offline development, cost optimization

### Example 3: Production (OpenAI)

```bash
# .env
JD_FIT_ENV=prod
JD_FIT_LOG_LEVEL=INFO
JD_FIT_OUT_DIR=/var/lib/jd-fit/out

JD_FIT_EMBEDDINGS__PROVIDER=openai
JD_FIT_EMBEDDINGS__MODEL=text-embedding-3-large
JD_FIT_EMBEDDINGS__DIM=3072
JD_FIT_EMBEDDINGS__BATCH_SIZE=128
JD_FIT_EMBEDDINGS__TIMEOUT_S=120

JD_FIT_LLM__PROVIDER=openai
JD_FIT_LLM__MODEL=gpt-4o
JD_FIT_LLM__TEMPERATURE=0.05
JD_FIT_LLM__MAX_TOKENS=2048
JD_FIT_LLM__TIMEOUT_S=120

OPENAI_API_KEY=sk-prod-key-here
```

**Use Case:** High-quality production scoring with best-available models

### Example 4: Cost-Optimized Production

```bash
# .env
JD_FIT_ENV=prod
JD_FIT_LOG_LEVEL=WARNING

# Ollama for embeddings (free)
JD_FIT_EMBEDDINGS__PROVIDER=ollama
JD_FIT_EMBEDDINGS__MODEL=nomic-embed-text
JD_FIT_EMBEDDINGS__DIM=768

# OpenAI for rationales only (lower volume)
JD_FIT_LLM__PROVIDER=openai
JD_FIT_LLM__MODEL=gpt-4o-mini
JD_FIT_LLM__TEMPERATURE=0.1

OPENAI_API_KEY=sk-prod-key-here
```

**Use Case:** Balance cost and quality by using local embeddings with cloud LLM

## Troubleshooting

### Configuration Not Loading

**Issue:** Environment variables not recognized

**Solutions:**
1. Verify `.env` file is in project root (same directory as `pyproject.toml`)
2. Check variable names use `JD_FIT_` prefix and double underscore `__` for nesting
3. Reload shell environment: `source .venv/bin/activate`
4. Verify with: `python -c "from jd_fit_evaluator.config import cfg; print(cfg.model_dump())"`

### Provider Connection Errors

**Issue:** `ConnectionError` when using Ollama

**Solutions:**
1. Verify Ollama is running: `ollama list`
2. Start Ollama service: `ollama serve`
3. Check host configuration: `echo $OLLAMA_HOST` (default: `http://localhost:11434`)
4. Test connection: `curl http://localhost:11434/api/tags`

**Issue:** `AuthenticationError` when using OpenAI

**Solutions:**
1. Verify API key is set: `echo $OPENAI_API_KEY`
2. Check key validity at [OpenAI dashboard](https://platform.openai.com/api-keys)
3. Ensure key has correct permissions and quota
4. Test with: `curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"`

### Invalid Configuration Values

**Issue:** `ValidationError` on startup

**Solutions:**
1. Check configuration constraints in error message
2. Verify numeric values are within valid ranges
3. Ensure provider is one of: `openai`, `ollama`, `mock`
4. Review configuration schema in [src/jd_fit_evaluator/config.py](../src/jd_fit_evaluator/config.py)

### Legacy Variable Conflicts

**Issue:** Unexpected behavior with both old and new variables set

**Solutions:**
1. Remove all `EMBED_*` legacy variables
2. Use only `JD_FIT_*` variables going forward
3. Check for conflicts: `env | grep -E "(EMBED_|JD_FIT_)"`

## Configuration Schema

The complete configuration schema is defined in [src/jd_fit_evaluator/config.py](../src/jd_fit_evaluator/config.py):

```python
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
    embeddings: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
```

---

**Last Updated:** 2025-10-03
**Related Documentation:**
- [README.md](../README.md) - Main documentation
- [src/jd_fit_evaluator/config.py](../src/jd_fit_evaluator/config.py) - Configuration implementation
