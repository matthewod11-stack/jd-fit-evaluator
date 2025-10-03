# Legacy Archive - DO NOT USE

**Warning: These files are deprecated and should not be imported or used.**

This directory contains legacy modules that have been moved from the `src/` directory to eliminate dual architecture and import confusion. All functionality has been migrated to the `src/jd_fit_evaluator/` package.

## Archived Files

- `legacy_cli.py` - Old CLI implementation (moved from `src/cli.py`)
- `legacy_config.py` - Old configuration module (moved from `src/config.py`)
- `legacy_embeddings.py` - Old embeddings implementation (moved from `src/models/embeddings.py`)

## Migration Guide

**Instead of:**

```python
from src.cli import score
from src.config import settings, LLM_MODEL
from src.models.embeddings import get_embedder
```

**Use:**

```python
from jd_fit_evaluator.cli import score
from jd_fit_evaluator.config import settings, LLM_MODEL
from jd_fit_evaluator.models.embeddings import get_embedder
```

All imports should now reference the unified `jd_fit_evaluator` package located in `src/jd_fit_evaluator/`.

---
*Archived on: $(date)*
*Reason: Eliminate dual architecture and consolidate to single package structure*