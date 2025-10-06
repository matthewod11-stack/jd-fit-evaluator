# Migration Guide: Legacy to Unified Architecture

## Overview

This guide documents the transformation of the JD-Fit Evaluator from a collection of loosely coupled scripts to a unified Python package architecture. It provides before/after examples, explains the rationale for changes, and helps developers understand the migration path.

## Why This Migration Was Necessary

### Problems with the Legacy Architecture

1. **Import Chaos**: Mixed import patterns (`from src.`, `from scoring.`, `sys.path` hacks)
2. **Package Structure**: No clear package boundaries or namespace organization
3. **Dependency Management**: Scattered configuration and inconsistent provider handling
4. **Testing Difficulties**: Hard to mock, test, and validate individual components
5. **Deployment Issues**: Difficult to package and distribute as a proper Python package

### Benefits of the Unified Architecture

1. **Clear Package Boundaries**: All code under `jd_fit_evaluator` namespace
2. **Consistent Import Patterns**: Standard Python package imports throughout
3. **Better Testability**: Proper dependency injection and mocking capabilities
4. **Professional Distribution**: Can be installed via pip and distributed properly
5. **Maintainability**: Clear module responsibilities and relationships

## Migration Examples

### 1. Import Pattern Transformations

#### Before (Legacy Patterns)

```python
# ❌ Legacy: Direct src imports
from src.scoring.features import extract_features
from src.models.embeddings import get_embeddings

# ❌ Legacy: Relative scoring imports
from scoring.weights import get_weights
from scoring.finalize import compute_fit_score

# ❌ Legacy: sys.path hacks
import sys
sys.path.insert(0, "src")
from scoring.features import extract_features
```

#### After (Unified Package)

```python
# ✅ Unified: Package-relative imports (within package)
from .scoring.features import extract_features
from .models.embeddings import get_embeddings

# ✅ Unified: Absolute package imports (external modules)
from jd_fit_evaluator.scoring.weights import get_weights
from jd_fit_evaluator.scoring.finalize import compute_fit_score

# ✅ Unified: No sys.path manipulation needed
from jd_fit_evaluator.scoring.features import extract_features
```

### 2. Module Structure Changes

#### Before (Legacy Structure)

```
project/
├── src/
│   ├── scoring/
│   │   ├── features.py
│   │   ├── weights.py
│   │   └── finalize.py
│   ├── models/
│   │   ├── embeddings.py
│   │   └── llm.py
│   └── cli.py
├── tests/
│   ├── test_scoring.py    # Uses sys.path hacks
│   └── test_models.py     # Hard to import modules
└── main.py               # Entry point outside package
```

#### After (Unified Structure)

```
project/
├── src/
│   └── jd_fit_evaluator/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── scoring/
│       │   ├── __init__.py
│       │   ├── features.py
│       │   ├── weights.py
│       │   └── finalize.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── embeddings.py
│       │   └── llm.py
│       └── ...
├── tests/
│   ├── test_scoring.py    # Clean package imports
│   └── test_models.py     # Standard test patterns
└── pyproject.toml        # Modern Python packaging
```

### 3. Configuration Migration

#### Before (Legacy Configuration)

```python
# ❌ Legacy: Scattered configuration
# config.py
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-ada-002"

# models/embeddings.py
if os.getenv("USE_OLLAMA"):
    provider = "ollama"
else:
    provider = "openai"

# scoring/weights.py
SKILLS_WEIGHT = 0.3  # Hardcoded weights
```

#### After (Unified Configuration)

```python
# ✅ Unified: Centralized Pydantic configuration
# config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    embedding_provider: str = "mock"
    llm_provider: str = "mock"
    openai_api_key: Optional[str] = None
    ollama_base_url: str = "http://localhost:11434"
    
    class Config:
        env_prefix = "JD_FIT_"

# Usage throughout the codebase
from jd_fit_evaluator.config import get_settings
settings = get_settings()
```

### 4. Test Migration

#### Before (Legacy Tests)

```python
# ❌ Legacy: sys.path manipulation
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from scoring.features import extract_features  # Direct import
```

#### After (Unified Tests)

```python
# ✅ Unified: Clean package imports
from jd_fit_evaluator.scoring.features import extract_features

# ✅ Unified: Proper test fixtures and mocking
@pytest.fixture
def mock_settings():
    return Settings(
        embedding_provider="mock",
        llm_provider="mock"
    )
```

### 5. CLI Migration

#### Before (Legacy CLI)

```python
# ❌ Legacy: main.py at root level
import sys
sys.path.insert(0, "src")

from scoring.features import extract_features
from models.embeddings import get_embeddings

def main():
    # CLI logic mixed with imports
    pass
```

#### After (Unified CLI)

```python
# ✅ Unified: CLI as package module
# src/jd_fit_evaluator/cli.py
from .scoring.features import extract_features
from .models.embeddings import get_embeddings

def main():
    # Clean CLI logic
    pass

# ✅ Entry point in pyproject.toml
[project.scripts]
jd-fit = "jd_fit_evaluator.cli:main"
```

## Step-by-Step Migration Process

### Phase 1: Package Structure Setup

1. **Create package structure**:
   ```bash
   mkdir -p src/jd_fit_evaluator
   touch src/jd_fit_evaluator/__init__.py
   ```

2. **Move modules into package**:
   ```bash
   mv src/scoring src/jd_fit_evaluator/
   mv src/models src/jd_fit_evaluator/
   mv src/cli.py src/jd_fit_evaluator/
   ```

3. **Add `__init__.py` files**:
   ```bash
   find src/jd_fit_evaluator -type d -exec touch {}/__init__.py \;
   ```

### Phase 2: Import Transformation

1. **Update internal imports** (within package):
   ```python
   # Change: from scoring.features import extract_features
   # To:     from .scoring.features import extract_features
   ```

2. **Update external imports** (from outside package):
   ```python
   # Change: from src.scoring.features import extract_features
   # To:     from jd_fit_evaluator.scoring.features import extract_features
   ```

3. **Remove sys.path hacks**:
   ```python
   # Remove: sys.path.insert(0, "src")
   # Use:    from jd_fit_evaluator.module import function
   ```

### Phase 3: Configuration Unification

1. **Create centralized config**:
   ```python
   # src/jd_fit_evaluator/config.py
   from pydantic_settings import BaseSettings
   ```

2. **Update all modules to use unified config**:
   ```python
   from .config import get_settings
   ```

### Phase 4: Test Migration

1. **Update test imports**:
   ```python
   from jd_fit_evaluator.module import function
   ```

2. **Add proper test fixtures**:
   ```python
   @pytest.fixture
   def settings():
       return Settings(embedding_provider="mock")
   ```

### Phase 5: Packaging

1. **Create `pyproject.toml`**:
   ```toml
   [project]
   name = "jd-fit-evaluator"
   
   [project.scripts]
   jd-fit = "jd_fit_evaluator.cli:main"
   ```

2. **Install in development mode**:
   ```bash
   pip install -e .
   ```

## Common Migration Issues and Solutions

### Issue 1: Import Errors After Migration

**Problem**: `ModuleNotFoundError: No module named 'scoring'`

**Cause**: Using legacy import patterns after migration

**Solution**:
```python
# Change from:
from scoring.features import extract_features

# To:
from jd_fit_evaluator.scoring.features import extract_features
```

### Issue 2: Circular Import Dependencies

**Problem**: `ImportError: cannot import name 'X' from partially initialized module`

**Cause**: Circular dependencies between modules

**Solution**:
1. Move shared utilities to a separate module
2. Use type checking imports: `if TYPE_CHECKING:`
3. Import functions inside functions when needed

### Issue 3: Test Discovery Issues

**Problem**: `pytest` can't find tests after migration

**Cause**: Test imports don't work with new package structure

**Solution**:
```python
# In conftest.py or test files
import sys
from pathlib import Path

# Add src to path for development testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
```

### Issue 4: Entry Point Not Working

**Problem**: `jd-fit` command not found after installation

**Cause**: Entry point not properly configured

**Solution**:
```toml
# In pyproject.toml
[project.scripts]
jd-fit = "jd_fit_evaluator.cli:main"
```

### Issue 5: Configuration Not Loading

**Problem**: Settings not being picked up from environment

**Cause**: Environment variable prefix not set correctly

**Solution**:
```python
class Settings(BaseSettings):
    class Config:
        env_prefix = "JD_FIT_"  # Ensures JD_FIT_* vars are loaded
```

## Validation Commands

### Before Migration (These Should Fail)

```bash
# Import violations should be detected
grep -r "from src\." src/ tests/
grep -r "sys\.path" src/ tests/

# Package installation should fail
pip install -e .
```

### After Migration (These Should Pass)

```bash
# No import violations
make guardpaths

# All tests pass
pytest

# Package installs cleanly
pip install -e .

# CLI works
jd-fit --help

# Smoke test passes
bash scripts/smoke_final_run.sh
```

## Rollback Procedure

If migration causes critical issues:

1. **Checkout previous working commit**:
   ```bash
   git checkout HEAD~1
   ```

2. **Preserve any data/configuration changes**:
   ```bash
   git stash
   git checkout main
   git stash pop
   ```

3. **Identify specific issues**:
   ```bash
   pytest -v
   make guardpaths
   ```

4. **Fix issues incrementally**:
   - Fix one module at a time
   - Test after each change
   - Commit working states

## Best Practices for Future Development

### 1. Always Use Package Imports

```python
# ✅ Good: Package imports
from jd_fit_evaluator.scoring.features import extract_features

# ❌ Bad: sys.path manipulation
sys.path.insert(0, "src")
from scoring.features import extract_features
```

### 2. Keep Modules Focused

Each module should have a single, clear responsibility:
- `scoring/features.py`: Feature extraction only
- `models/embeddings.py`: Embedding provider logic only
- `config.py`: Configuration management only

### 3. Use Dependency Injection

```python
# ✅ Good: Dependency injection
def score_candidate(candidate: dict, settings: Settings) -> float:
    embeddings = get_embeddings(settings)
    return compute_score(candidate, embeddings)

# ❌ Bad: Hard dependencies
def score_candidate(candidate: dict) -> float:
    embeddings = get_embeddings()  # Hard dependency
    return compute_score(candidate, embeddings)
```

### 4. Write Migration-Safe Tests

```python
# ✅ Good: Tests that work with package structure
from jd_fit_evaluator.scoring.features import extract_features

def test_feature_extraction():
    result = extract_features(candidate_data)
    assert result is not None

# ❌ Bad: Tests with sys.path dependencies
import sys
sys.path.insert(0, "src")
from scoring.features import extract_features
```

## Migration Checklist

- [ ] Package structure created (`src/jd_fit_evaluator/`)
- [ ] All `__init__.py` files added
- [ ] Internal imports updated (`.module` pattern)
- [ ] External imports updated (`jd_fit_evaluator.module` pattern)
- [ ] All `sys.path` hacks removed
- [ ] Configuration unified (`config.py`)
- [ ] Tests updated with package imports
- [ ] `pyproject.toml` configured properly
- [ ] Entry points working (`jd-fit` command)
- [ ] All tests passing
- [ ] Import violations check passes (`make guardpaths`)
- [ ] Smoke test passes
- [ ] Documentation updated

## Getting Help

If you encounter issues during migration:

1. **Check the validation commands** above
2. **Review common issues** and solutions in this guide
3. **Run the smoke test** to validate end-to-end functionality
4. **Check git history** for examples of successful migrations
5. **Create an issue** with specific error messages and context

Remember: The migration to unified architecture improves code quality, testability, and maintainability. The short-term effort pays dividends in long-term development productivity.