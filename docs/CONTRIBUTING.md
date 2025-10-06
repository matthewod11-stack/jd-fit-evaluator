# Contributing Guide

## Welcome

Thank you for your interest in contributing to the JD-Fit Evaluator! This guide will help you understand our development process, code standards, and how to make effective contributions.

## Quick Start for Contributors

### 1. Development Setup

```bash
# Clone the repository
git clone https://github.com/matthewod11-stack/jd-fit-evaluator.git
cd jd-fit-evaluator

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with development dependencies
pip install -e ".[dev]"

# Install git hooks for code quality
bash scripts/install_hooks.sh

# Verify setup
make health
pytest
```

### 2. Validate Your Environment

```bash
# Run smoke test to ensure everything works
bash scripts/smoke_final_run.sh

# Check code quality
make guardpaths    # Import pattern validation
ruff check        # Linting
pytest            # Test suite
```

## Code Standards

### Import Rules (Strictly Enforced)

**✅ Correct Patterns:**

```python
# Within the jd_fit_evaluator package (relative imports)
from .models.embeddings import get_embeddings
from .scoring.features import extract_features
from .config import get_settings

# From external modules (absolute imports)
from jd_fit_evaluator.cli import main
from jd_fit_evaluator.scoring.finalize import compute_fit_score

# Standard library and third-party imports
import os
from pathlib import Path
from typing import Optional, Dict, List
import pandas as pd
```

**❌ Prohibited Patterns:**

```python
# Legacy src.* imports (breaks package encapsulation)
from src.scoring.features import extract_features

# Direct module imports (bypasses package namespace)
from scoring.weights import get_weights
from models.embeddings import get_embeddings

# sys.path manipulation (breaks proper packaging)
import sys
sys.path.insert(0, "src")
from scoring.features import extract_features
```

### Code Style Guidelines

#### 1. Python Style

We follow PEP 8 with these specific conventions:

```python
# Use type hints for all public functions
def extract_features(candidate: Dict[str, Any], settings: Settings) -> Dict[str, float]:
    """Extract numerical features from candidate data.
    
    Args:
        candidate: Structured candidate information
        settings: Configuration settings
        
    Returns:
        Dictionary of feature names to values
    """
    pass

# Use dataclasses or Pydantic models for structured data
@dataclass
class CandidateProfile:
    candidate_id: str
    name: str
    skills: List[str]
    experience_years: float

# Use context managers for resources
def process_resumes(directory: Path) -> None:
    with open(directory / "manifest.json") as f:
        manifest = json.load(f)
```

#### 2. Error Handling

```python
# Use specific exceptions with helpful messages
class ScoringError(Exception):
    """Raised when candidate scoring fails."""
    pass

# Provide actionable error messages
def score_candidate(candidate: dict) -> float:
    if not candidate.get("skills"):
        raise ScoringError(
            "Cannot score candidate without skills. "
            "Ensure resume parsing extracted skills properly."
        )
```

#### 3. Configuration Management

```python
# Always use the centralized Settings class
from jd_fit_evaluator.config import get_settings

def my_function():
    settings = get_settings()
    if settings.embedding_provider == "openai":
        # Use OpenAI provider
        pass
```

#### 4. Testing Standards

```python
# Use descriptive test names
def test_feature_extraction_handles_missing_skills():
    candidate = {"name": "John Doe"}  # No skills
    result = extract_features(candidate)
    assert result["skills_count"] == 0

# Use fixtures for common test data
@pytest.fixture
def sample_candidate():
    return {
        "candidate_id": "test_001",
        "name": "Jane Doe",
        "skills": ["Python", "Machine Learning"],
        "experience_years": 5.0
    }

# Mock external dependencies
@patch('jd_fit_evaluator.models.embeddings.openai_client')
def test_embedding_generation_with_mock(mock_client):
    mock_client.embeddings.create.return_value = Mock(data=[Mock(embedding=[0.1, 0.2])])
    result = get_embeddings(["test text"])
    assert len(result) == 1
```

## Development Workflow

### 1. Creating a New Feature

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes following code standards
# Write tests for new functionality
# Update documentation if needed

# Validate changes
make guardpaths    # Check import patterns
pytest            # Run test suite
ruff check        # Check linting

# Commit changes
git add .
git commit -m "feat: add new feature description"

# Push and create PR
git push origin feature/your-feature-name
```

### 2. Bug Fixes

```bash
# Create bugfix branch
git checkout -b bugfix/issue-description

# Write failing test that reproduces the bug
pytest tests/test_module.py::test_specific_case -v

# Fix the bug
# Ensure test now passes
# Add additional tests if needed

# Validate fix
make guardpaths
pytest
ruff check

# Commit with descriptive message
git commit -m "fix: resolve issue with specific component"
```

### 3. Pre-commit Validation

Our git hooks automatically run these checks:

```bash
# Import pattern validation
make guardpaths

# Test suite
pytest --tb=short

# Code linting
ruff check

# If any check fails, the commit is blocked
```

## Pull Request Process

### 1. PR Requirements

**Before submitting a PR:**

- [ ] All tests pass (`pytest`)
- [ ] No import violations (`make guardpaths`)
- [ ] Code follows style guidelines (`ruff check`)
- [ ] Smoke test passes (`bash scripts/smoke_final_run.sh`)
- [ ] Documentation updated if needed
- [ ] PR description explains changes clearly

### 2. PR Template

Use this template for your PR description:

```markdown
## Description
Brief description of the changes and why they were made.

## Changes Made
- List specific changes
- Include any breaking changes
- Note any new dependencies

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Smoke test passes
- [ ] Manual testing completed

## Documentation
- [ ] Code comments updated
- [ ] Documentation files updated
- [ ] README updated if needed

## Validation
- [ ] `make guardpaths` passes
- [ ] `pytest` passes
- [ ] `ruff check` passes
- [ ] `bash scripts/smoke_final_run.sh` passes
```

### 3. Review Process

1. **Automated Checks**: GitHub Actions will run validation
2. **Code Review**: Maintainers will review for:
   - Code quality and style
   - Test coverage and quality
   - Documentation completeness
   - Performance implications
   - Security considerations

3. **Feedback**: Address review comments promptly
4. **Approval**: Requires approval from at least one maintainer
5. **Merge**: Squash and merge is preferred for clean history

## Testing Guidelines

### Test Categories

#### 1. Unit Tests

Test individual functions and classes in isolation:

```python
# tests/test_scoring_features.py
def test_extract_skills_feature():
    candidate = {"skills": ["Python", "SQL", "Docker"]}
    features = extract_features(candidate)
    assert features["skills_count"] == 3
    assert "python" in features["skills_normalized"]
```

#### 2. Integration Tests

Test component interactions:

```python
# tests/test_scoring_integration.py
def test_end_to_end_scoring():
    candidate_data = load_test_candidate()
    score = score_candidate(candidate_data)
    assert 0.0 <= score <= 1.0
    assert isinstance(score, float)
```

#### 3. End-to-End Tests

Test complete workflows:

```python
# tests/e2e/test_cli_workflows.py
def test_score_sample_workflow():
    result = subprocess.run([
        "python", "-m", "jd_fit_evaluator.cli", 
        "score", "--sample", "--role", "Software Engineer"
    ], capture_output=True, text=True)
    assert result.returncode == 0
    assert "scored successfully" in result.stdout
```

### Test Data Management

```python
# Use fixtures for reusable test data
@pytest.fixture
def sample_resume_text():
    return """
    John Doe
    Software Engineer
    Skills: Python, JavaScript, React
    Experience: 5 years at Tech Corp
    """

# Store golden test data in version control
def test_scoring_regression():
    candidate = load_golden_candidate("software_engineer_001")
    score = score_candidate(candidate)
    # Allow small floating point variations
    assert abs(score - 0.85) < 0.01
```

## Architecture Guidelines

### Module Organization

Follow these principles when organizing code:

```python
# Each module should have a single responsibility
# scoring/features.py - Feature extraction only
# models/embeddings.py - Embedding provider logic only
# config.py - Configuration management only

# Use dependency injection for testability
def score_candidate(candidate: dict, embeddings_provider: EmbeddingProvider) -> float:
    embeddings = embeddings_provider.get_embeddings(candidate["text"])
    return compute_score(candidate, embeddings)

# Avoid global state and singletons
# Use configuration objects instead
def process_batch(candidates: List[dict], settings: Settings) -> List[float]:
    provider = get_embedding_provider(settings)
    return [score_candidate(c, provider) for c in candidates]
```

### Performance Considerations

```python
# Use generators for large datasets
def process_candidates_stream(manifest_path: Path) -> Iterator[Dict]:
    with open(manifest_path) as f:
        for line in f:
            yield json.loads(line)

# Implement caching for expensive operations
@lru_cache(maxsize=1000)
def get_cached_embedding(text: str) -> List[float]:
    return embedding_provider.embed(text)

# Use batch processing when possible
def score_batch(candidates: List[dict], batch_size: int = 32) -> List[float]:
    scores = []
    for i in range(0, len(candidates), batch_size):
        batch = candidates[i:i + batch_size]
        batch_scores = process_batch(batch)
        scores.extend(batch_scores)
    return scores
```

## Common Contribution Patterns

### Adding a New Scoring Feature

1. **Define the feature in `scoring/features.py`**:

```python
def extract_education_level(candidate: dict) -> float:
    """Extract education level as a numerical feature.
    
    Returns:
        0.0 = No formal education
        0.5 = Some college/associates
        1.0 = Bachelor's degree or higher
    """
    education = candidate.get("education", [])
    # Implementation details...
    return education_score
```

2. **Add tests in `tests/test_scoring_features.py`**:

```python
def test_extract_education_level():
    candidate_with_degree = {"education": [{"degree": "Bachelor's", "field": "CS"}]}
    assert extract_education_level(candidate_with_degree) == 1.0
    
    candidate_no_education = {"education": []}
    assert extract_education_level(candidate_no_education) == 0.0
```

3. **Update scoring weights in `scoring/weights.py`**:

```python
# Add new weight
EDUCATION_WEIGHT = 0.15

# Update weight calculation
def get_scoring_weights() -> Dict[str, float]:
    return {
        "skills": SKILLS_WEIGHT,
        "experience": EXPERIENCE_WEIGHT,
        "education": EDUCATION_WEIGHT,  # New weight
        # ... other weights
    }
```

### Adding a New Provider

1. **Implement provider interface**:

```python
# models/providers/new_provider.py
class NewEmbeddingProvider(EmbeddingProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # Implementation details...
        pass
```

2. **Add provider configuration**:

```python
# config.py
class Settings(BaseSettings):
    embedding_provider: str = "mock"
    new_provider_api_key: Optional[str] = None
    new_provider_endpoint: str = "https://api.example.com"
```

3. **Update provider factory**:

```python
# models/embeddings.py
def get_embedding_provider(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider == "new_provider":
        return NewEmbeddingProvider(settings)
    # ... other providers
```

## Debugging and Troubleshooting

### Common Issues

#### Import Errors

```bash
# Check for import violations
make guardpaths

# Common fixes:
# Change: from src.module import function
# To:     from jd_fit_evaluator.module import function

# Change: from module import function  
# To:     from .module import function  (within package)
```

#### Test Failures

```bash
# Run specific test with verbose output
pytest tests/test_module.py::test_function -v -s

# Run with debugger
pytest tests/test_module.py::test_function --pdb

# Check test coverage
pytest --cov=jd_fit_evaluator --cov-report=html
```

#### Configuration Issues

```bash
# Check current configuration
python -c "from jd_fit_evaluator.config import get_settings; print(get_settings())"

# Test with different providers
JD_FIT_EMBEDDING_PROVIDER=mock python -m jd_fit_evaluator.cli score --sample
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
# Set debug environment variable
export JD_FIT_LOG_LEVEL=DEBUG

# Run with verbose output
python -m jd_fit_evaluator.cli score --sample --verbose
```

## Documentation Standards

### Code Documentation

```python
def complex_function(param1: str, param2: Optional[int] = None) -> Dict[str, Any]:
    """One-line summary of what the function does.
    
    Longer description if needed. Explain the purpose, behavior,
    and any important implementation details.
    
    Args:
        param1: Description of the first parameter
        param2: Description of the optional parameter
        
    Returns:
        Description of the return value and its structure
        
    Raises:
        SpecificError: When this specific error occurs
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result["status"])
        "success"
    """
    pass
```

### README Updates

When adding new features, update the README sections:

- **Features**: List new capabilities
- **Usage**: Add examples of new commands or workflows
- **Configuration**: Document new settings
- **Troubleshooting**: Add common issues and solutions

## Release Process

### Version Numbering

We use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Checklist

- [ ] All tests pass on main branch
- [ ] Documentation updated
- [ ] Version number updated in `pyproject.toml`
- [ ] Changelog updated with release notes
- [ ] Git tag created
- [ ] Package built and tested
- [ ] Release notes published

## Getting Help

### Development Questions

1. **Check existing documentation** (README, docs/, code comments)
2. **Search issues** for similar problems or questions
3. **Run validation commands** to identify specific issues
4. **Create an issue** with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)

### Best Practices for Getting Help

```bash
# Include relevant command outputs
make guardpaths
pytest -v
python --version
pip list | grep jd-fit

# Include configuration details
echo $JD_FIT_EMBEDDING_PROVIDER
cat .env  # (redact sensitive values)
```

## Code of Conduct

- **Be respectful** in all interactions
- **Provide constructive feedback** in code reviews
- **Help newcomers** get started with the project
- **Focus on technical merit** in discussions
- **Assume positive intent** from contributors

## Recognition

Contributors are recognized in:

- **README.md**: Active contributors section
- **Release notes**: Feature/fix attribution
- **Git history**: Proper commit attribution
- **Issues/PRs**: Thanks and recognition comments

Thank you for contributing to the JD-Fit Evaluator! Your contributions help make this tool better for everyone.