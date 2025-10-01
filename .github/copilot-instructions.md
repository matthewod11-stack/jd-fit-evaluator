# JD-Fit Evaluator - AI Coding Agent Instructions

## Architecture Overview

This is a **multi-signal, JD-anchored candidate evaluation system** that scores resumes against job descriptions using weighted feature extraction and local embeddings.

**Core Data Flow:**
1. **Ingestion**: PDFs → individual candidate files → structured JSON
2. **Feature Extraction**: Parse resumes into signals (titles, industries, skills, tenure, context)
3. **Scoring**: Weighted combination of features → 0-100 fit score + rationale
4. **Interfaces**: CLI, FastAPI, Streamlit UI

## Key Components & Boundaries

- **`src/etl/`**: Data ingestion (Greenhouse API + file-based resume splitting)
- **`src/parsing/`**: Resume text extraction and stint/title normalization
- **`src/models/embeddings.py`**: Local LLaMA embeddings with deterministic fallback
- **`src/scoring/`**: Multi-signal feature extraction + weighted scoring + rationale generation
- **`app/api.py`**: FastAPI wrapper for programmatic access
- **`ui/app.py`**: Streamlit reviewer interface
- **`tools/`**: Batch processing utilities for PDF splitting and manifest creation

## Critical Workflows

**Setup**: Always use `make setup` or the VS Code task "Setup (venv + deps)" - this creates the venv and installs dependencies.

**File-based Resume Processing** (primary workflow):
```bash
# Split multi-resume PDF into individual files + manifest
make split-batch INPUT=data/raw/batch-01/all_resumes.pdf BATCH=batch-01

# Score candidates against JD
make score-sample  # uses sample data
make score         # uses data/ingest/*.json files
```

**Testing Approach**: Direct imports (`test_direct.py`) bypass CLI for unit testing core scoring logic. Always add `sys.path.insert(0, "src")` for direct module imports.

## Project-Specific Patterns

**Data Structures**:
- **Candidate JSON**: `{candidate_id, name, stints: [{company, title, industry, start, end}], skills: [str], ...}`
- **Role Definition**: Extracted from structured JD text with `Title:`, `Level:`, `Industries:`, `Must-have:`, `Nice-to-have:` markers
- **Scoring Output**: `{fit_score: float, rationale: [str], component_scores: {...}}`

**Configuration**: Uses Pydantic `Settings` with `.env` fallback. Greenhouse integration is deprecated/disabled (`ENABLE_GH=1` required).

**Embeddings Strategy**: Graceful degradation - attempts local GGUF model loading, falls back to deterministic hash-based embeddings for consistent testing without GPU requirements.

**Feature Engineering**: Multi-signal approach in `src/scoring/features.py`:
- Title/level matching with soft penalties
- Industry relevance scoring
- Semantic skill similarity via embeddings
- Context disambiguation (hiring vs being recruited)
- Tenure patterns (average, last stint, consistency)
- Recency scoring and bonus flags

## Integration Points

**File Processing**: `tools/split_resumes_and_manifest.py` handles PDF→individual resume conversion with candidate manifest generation.

**API Contracts**: FastAPI uses Pydantic models (`Role`, `Candidate`) - maintain compatibility when modifying data structures.

**Weight Configuration**: Scoring weights in `src/scoring/weights.py` are configurable per role/JD for reproducibility.

**Testing**: Run `make health` to verify core dependencies. Use `pytest` for test execution, direct imports for isolated component testing.

## Development Conventions

- **Error Handling**: Graceful fallbacks (embeddings, model loading) rather than hard failures
- **Path Handling**: Use `pathlib.Path` throughout, absolute paths in tools
- **CLI Pattern**: Typer-based with `load_role_from_jd()` and `load_sample_candidate()` utilities
- **Data Persistence**: JSON for candidates, CSV for manifests, structured text for JDs
- **Logging**: Minimal - focus on user-facing feedback via CLI/UI rather than debug logs