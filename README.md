# JD-Fit Evaluator

**A multi-signal, JD-anchored candidate evaluation system** that computes absolute fit to a Job Description and returns 0–100 Fit Scores with concise rationales.

## 📖 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [CLI Commands](#cli-commands)
  - [Common Workflows](#common-workflows)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Documentation](#documentation)
- [Development](#development)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Legal & Ethics](#legal--ethics)

## Overview

JD-Fit Evaluator is a production-ready candidate screening system that combines multiple signals to evaluate candidate-job fit:

- **Multi-signal scoring**: titles/level, industries/companies, tenure, skills (semantic), context disambiguation, recency, bonus flags
- **Flexible embeddings**: OpenAI, Ollama, or mock providers with graceful fallbacks
- **Fine-tuning support**: Classical ML models (LogReg/XGBoost) trained on historical labels
- **Multiple interfaces**: CLI, FastAPI REST API, and Streamlit UI

## Features

✅ **Resume Parsing**: Extract structured data from PDF, DOCX, and text resumes
✅ **Semantic Skills Matching**: Compare candidate skills to JD requirements using embeddings
✅ **Multi-Signal Scoring**: Title matching, industry alignment, tenure analysis, context disambiguation
✅ **LLM-Powered Rationales**: Generate human-readable explanations for scores
✅ **Batch Processing**: Score multiple candidates efficiently with parallel processing
✅ **Training Pipeline**: Fine-tune scoring models on your historical hiring data
✅ **Interactive UI**: Review candidates with the Streamlit dashboard
✅ **REST API**: Integrate scoring into your existing tools and workflows

## Quick Start

```bash
# 1. Clone and enter the project directory
cd jd-fit-evaluator

# 2. Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e .

# 3. Try the sample scoring (no setup needed!)
python -m jd_fit_evaluator.cli score --sample --role "Senior Product Designer"

# 4. View results in the UI
python -m jd_fit_evaluator.cli ui
```

That's it! The sample workflow uses pre-parsed candidate data and requires no configuration.

## Installation

### Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Virtual environment** (recommended)
- **Optional**: Ollama (for local LLM embeddings)

### Standard Installation

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package with dependencies
pip install -e .
```

### Development Installation

```bash
# Install with dev dependencies
pip install -e .[dev]

# Run tests to verify installation
pytest

# Run linting
ruff check src tests
```

### Optional: Ollama Setup for Local LLMs

For local embeddings and LLM processing without external APIs:

```bash
# Install Ollama (macOS/Linux)
curl https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3.1

# Configure JD-Fit to use Ollama
export JD_FIT_EMBEDDINGS__PROVIDER=ollama
export JD_FIT_EMBEDDINGS__MODEL=llama3.1
export JD_FIT_LLM__PROVIDER=ollama
export JD_FIT_LLM__MODEL=llama3.1
```

## Configuration

JD-Fit Evaluator uses environment variables with the `JD_FIT_` prefix. All settings are optional with sensible defaults.

### Configuration File

Create a `.env` file in the project root:

```bash
# Environment
JD_FIT_ENV=dev
JD_FIT_LOG_LEVEL=INFO
JD_FIT_OUT_DIR=out

# Embeddings (OpenAI, Ollama, or Mock)
JD_FIT_EMBEDDINGS__PROVIDER=mock
JD_FIT_EMBEDDINGS__MODEL=text-embedding-3-small
JD_FIT_EMBEDDINGS__DIM=1536
JD_FIT_EMBEDDINGS__BATCH_SIZE=256
JD_FIT_EMBEDDINGS__TIMEOUT_S=60

# LLM for parsing and rationales
JD_FIT_LLM__PROVIDER=mock
JD_FIT_LLM__MODEL=llama3.1
JD_FIT_LLM__TEMPERATURE=0.1
JD_FIT_LLM__MAX_TOKENS=4096
JD_FIT_LLM__TIMEOUT_S=60
```

### Configuration Options

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `JD_FIT_ENV` | Environment name | `dev` | `dev`, `prod` |
| `JD_FIT_OUT_DIR` | Output directory | `out` | Any valid path |
| `JD_FIT_LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `JD_FIT_EMBEDDINGS__PROVIDER` | Embedding backend | `mock` | `openai`, `ollama`, `mock` |
| `JD_FIT_EMBEDDINGS__MODEL` | Model name | `text-embedding-3-small` | Provider-specific |
| `JD_FIT_EMBEDDINGS__DIM` | Embedding dimensions | `1536` | `1-4096` |
| `JD_FIT_EMBEDDINGS__BATCH_SIZE` | Batch processing size | `256` | `1-1024` |
| `JD_FIT_LLM__PROVIDER` | LLM backend | `mock` | `openai`, `ollama`, `mock` |
| `JD_FIT_LLM__MODEL` | LLM model name | `llama3.1` | Provider-specific |
| `JD_FIT_LLM__TEMPERATURE` | Generation temperature | `0.1` | `0.0-2.0` |
| `JD_FIT_LLM__MAX_TOKENS` | Max generation tokens | `4096` | `1-32000` |

### Provider-Specific Configuration

#### OpenAI

```bash
JD_FIT_EMBEDDINGS__PROVIDER=openai
JD_FIT_EMBEDDINGS__MODEL=text-embedding-3-small
JD_FIT_LLM__PROVIDER=openai
JD_FIT_LLM__MODEL=gpt-4
OPENAI_API_KEY=your_api_key_here
```

#### Ollama (Local)

```bash
JD_FIT_EMBEDDINGS__PROVIDER=ollama
JD_FIT_EMBEDDINGS__MODEL=llama3.1
JD_FIT_LLM__PROVIDER=ollama
JD_FIT_LLM__MODEL=llama3.1
OLLAMA_HOST=http://localhost:11434  # Default, can be omitted
```

#### Mock (Testing/Development)

```bash
JD_FIT_EMBEDDINGS__PROVIDER=mock
JD_FIT_LLM__PROVIDER=mock
# No additional configuration needed - uses deterministic fallbacks
```

## Usage

### CLI Commands

JD-Fit Evaluator provides a comprehensive CLI for all operations:

#### `score` - Score Candidates

Score candidates against a job description:

```bash
# Score sample candidates (no setup required)
python -m jd_fit_evaluator.cli score --sample --role "Senior Product Designer"

# Score candidates from a directory
python -m jd_fit_evaluator.cli score data/parsed --role "Senior Product Designer" -o out/scores

# Score with detailed explanations
python -m jd_fit_evaluator.cli score data/parsed --role "Senior Product Designer" --explain
```

**Options:**
- `candidates` - Path to directory, JSON, or JSONL file (or use `--sample`)
- `--role, -r` - Role/title description (required)
- `--sample` - Use built-in sample data
- `--explain` - Generate detailed rationales
- `--out, -o` - Output directory (default: `out`)
- `--strict` - Fail on validation errors (default: True)

#### `parse` - Parse Resumes

Extract structured data from raw resume files:

```bash
# Parse all resumes in a directory
python -m jd_fit_evaluator.cli parse data/raw/resumes -o data/parsed

# Parse without LLM (faster, less accurate)
python -m jd_fit_evaluator.cli parse data/raw/resumes --no-use-llm
```

**Options:**
- `input_dir` - Directory containing PDF/DOCX/TXT resumes
- `--out, -o` - Output directory (default: `out`)
- `--use-llm` - Use LLM for enhanced parsing (default: True)

#### `pipeline` - End-to-End Processing

Run the complete pipeline from raw resumes to scores:

```bash
# Rename → Parse → Score in one command
python -m jd_fit_evaluator.cli pipeline data/raw/resumes \
  --role "Senior Product Designer" \
  --use-llm \
  --explain \
  -o out/complete
```

**Options:**
- `input_dir` - Directory with raw resume files
- `--role, -r` - Role description (required)
- `--out, -o` - Output directory
- `--use-llm` - Use LLM for parsing
- `--explain` - Generate score explanations

#### `rename` - Standardize Filenames

Rename resume files to a consistent format:

```bash
python -m jd_fit_evaluator.cli rename data/raw/resumes
```

#### `ui` - Launch Streamlit UI

Start the interactive candidate reviewer:

```bash
python -m jd_fit_evaluator.cli ui
# Opens browser at http://localhost:8501
```

Or use the Makefile shortcut:

```bash
make ui
```

#### `train` - Train Scoring Model

Fine-tune the scoring model on labeled data:

```bash
python -m jd_fit_evaluator.cli train \
  --scores out/scores/scores.json \
  --labels data/labels/labels.csv \
  --out models/trained_model.pkl
```

**Labels CSV format:**
```csv
candidate_id,label
cand_001,1
cand_002,0
cand_003,1
```

### Common Workflows

#### 1. Quick Evaluation (Sample Data)

Test the system with built-in sample data:

```bash
# Score sample candidates
python -m jd_fit_evaluator.cli score --sample --role "Senior Product Designer"

# View results in UI
python -m jd_fit_evaluator.cli ui
```

#### 2. Batch Processing New Candidates

Process a batch of resumes from PDFs:

```bash
# Step 1: Parse resumes
python -m jd_fit_evaluator.cli parse data/raw/batch_01 -o data/parsed/batch_01

# Step 2: Score candidates
python -m jd_fit_evaluator.cli score data/parsed/batch_01 \
  --role "Senior Product Designer" \
  --explain \
  -o out/batch_01

# Step 3: Review in UI
python -m jd_fit_evaluator.cli ui
```

#### 3. End-to-End Pipeline

Process resumes in one command:

```bash
python -m jd_fit_evaluator.cli pipeline data/raw/batch_01 \
  --role "Senior Product Designer" \
  --use-llm \
  --explain \
  -o out/batch_01
```

#### 4. Training Custom Models

Improve scoring with your historical data:

```bash
# Step 1: Score candidates
python -m jd_fit_evaluator.cli score data/parsed --role "Product Designer" -o out/scores

# Step 2: Label candidates (manually edit labels.csv)
# Create data/labels.csv with candidate_id,label columns

# Step 3: Train model
python -m jd_fit_evaluator.cli train \
  --scores out/scores/scores.json \
  --labels data/labels.csv \
  --out models/custom_model.pkl

# Step 4: Use trained model (configure in weights.py)
```

#### 5. API Integration

Use the REST API for programmatic access:

```bash
# Start API server
python -m uvicorn app.api:app --reload

# Score candidates via API
curl -X POST "http://localhost:8000/score" \
  -H "Content-Type: application/json" \
  -d '{
    "candidates": [...],
    "role": "Senior Product Designer"
  }'
```

## Architecture

### Project Structure

```
jd-fit-evaluator/
├── src/
│   ├── jd_fit_evaluator/
│   │   ├── cli.py              # CLI commands and entry points
│   │   ├── config.py           # Configuration management
│   │   ├── etl/
│   │   │   ├── ingestion.py    # Resume ingestion
│   │   │   └── manifest_ingest.py  # Manifest-based ingestion
│   │   ├── parsing/
│   │   │   ├── llm_parser.py   # LLM-powered resume parsing
│   │   │   └── resume.py       # Text extraction
│   │   ├── models/
│   │   │   ├── embeddings.py   # Embedding providers
│   │   │   └── llm.py          # LLM clients
│   │   ├── scoring/
│   │   │   ├── features.py     # Feature extraction
│   │   │   ├── finalize.py     # Score calculation
│   │   │   ├── jd_profile.py   # JD parsing
│   │   │   ├── rationale_llm.py  # Score explanations
│   │   │   └── weights.py      # Scoring weights
│   │   ├── training/
│   │   │   └── train.py        # Model training
│   │   └── utils/
│   │       ├── errors.py       # Error handling
│   │       └── schema.py       # Data schemas
├── app/
│   └── api.py                  # FastAPI REST API
├── ui/
│   └── app.py                  # Streamlit dashboard
├── tests/                      # Test suite
├── data/
│   └── sample/                 # Sample data for quick start
├── docs/                       # Additional documentation
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Package configuration
└── Makefile                   # Common commands
```

### Data Flow

```
1. INGESTION
   Raw Resumes (PDF/DOCX) → Parse → Structured JSON

2. SCORING
   Structured Data + JD → Feature Extraction → Score Calculation → Results

3. TRAINING (Optional)
   Scores + Labels → Model Training → Updated Weights

4. OUTPUT
   Results → JSON/CSV → UI/API → Human Review
```

### Scoring Algorithm

JD-Fit uses a weighted multi-signal approach:

1. **Title Matching** (25%): Semantic similarity to JD titles
2. **Industry Alignment** (20%): Match to target industries
3. **Tenure Analysis** (20%): Average and recent stint duration
4. **Skills Matching** (25%): Embedding-based semantic similarity
5. **Context Disambiguation** (5%): Correct role interpretation
6. **Recency** (3%): Recent relevant experience
7. **Bonus Flags** (2%): Additional positive signals

Final score: Weighted sum normalized to 0-100 scale.

## API Reference

### REST API

Start the FastAPI server:

```bash
python -m uvicorn app.api:app --reload
# API available at http://localhost:8000
# Interactive docs at http://localhost:8000/docs
```

#### `POST /score`

Score candidates against a job description.

**Request:**
```json
{
  "candidates": [
    {
      "path": "resume.pdf",
      "parsed": {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "stints": [...]
      }
    }
  ],
  "role": "Senior Product Designer",
  "explain": true
}
```

**Response:**
```json
{
  "results": [
    {
      "candidate_id": "cand_001",
      "score": 85.5,
      "rationale": "Strong match...",
      "subscores": {
        "title": 90,
        "industry": 85,
        "tenure": 80,
        "skills": 88
      }
    }
  ]
}
```

### Programmatic Usage

```python
from jd_fit_evaluator.scoring.finalize import score_candidates

# Prepare candidate data
candidates = [{
    "path": "resume.pdf",
    "parsed": {
        "name": "Jane Doe",
        "stints": [...]
    }
}]

# Score candidates
results = score_candidates(
    candidates,
    role="Senior Product Designer",
    explain=True
)

# Process results
for result in results:
    print(f"{result.name}: {result.score}")
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

### Architecture & Design

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design principles, import rules, data flow, and module responsibilities
- **[docs/MIGRATION.md](docs/MIGRATION.md)** - Legacy to unified architecture transformation guide with before/after examples
- **[docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)** - Development guidelines, code standards, and PR process

### Configuration & Deployment

- **[docs/config.md](docs/config.md)** - Detailed configuration options and provider setup
- **[OPTIMIZED_FINAL_RUN_README.md](OPTIMIZED_FINAL_RUN_README.md)** - Batch processing and optimization guide

### Project Evolution

- **[docs/PRD_v1.md](docs/PRD_v1.md)** through **[docs/PRD_v1.3.md](docs/PRD_v1.3.md)** - Product requirements and evolution
- **[OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)** - Performance optimizations and benchmarks

## Development

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/matthewod11-stack/jd-fit-evaluator.git
cd jd-fit-evaluator

# Create virtual environment and install with dev dependencies
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Install git hooks for code quality enforcement
bash scripts/install_hooks.sh

# Verify setup
make health
pytest
```

### Code Quality Enforcement

The project uses automated checks to maintain code quality:

```bash
# Import pattern validation (no sys.path hacks, proper package imports)
make guardpaths

# Test suite with coverage
pytest --cov=jd_fit_evaluator

# Code linting and formatting
ruff check

# Batch processing validation (170+ candidates)
bash scripts/smoke_final_run.sh
```

### Git Hooks

Pre-commit hooks automatically run before each commit:

- **Import validation**: Ensures proper `jd_fit_evaluator.*` import patterns
- **Test execution**: Runs the full test suite
- **Linting**: Checks code style with ruff

Install hooks with: `bash scripts/install_hooks.sh`

### Key Development Commands

```bash
# Quick health check
make health

# Run sample scoring (no data needed)
make score

# Launch development UI
make ui

# Start API server
make api

# Run all validation checks
make guardpaths && pytest && ruff check
```

## Troubleshooting

### Common Issues

#### Installation Problems

**Error: `No module named 'jd_fit_evaluator'`**

```bash
# Solution: Install package in editable mode
pip install -e .
```

**Error: `pip install` fails with dependency conflicts**

```bash
# Solution: Use clean virtual environment
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

#### Configuration Issues

**Error: `Ollama connection refused`**

```bash
# Verify Ollama is running
ollama list

# Start Ollama service
ollama serve

# Check connection
curl http://localhost:11434/api/tags
```

**Error: `OpenAI API key not found`**

```bash
# Set API key in environment
export OPENAI_API_KEY=your_key_here

# Or add to .env file
echo "OPENAI_API_KEY=your_key_here" >> .env
```

#### Runtime Errors

**Error: `No parsed candidates found`**

```bash
# Check directory structure
ls -la data/sample/

# Ensure .parsed.json files exist
python -m jd_fit_evaluator.cli parse data/raw -o data/parsed
```

**Error: `UserInputError: Candidates path does not exist`**

```bash
# Use absolute path or verify relative path
python -m jd_fit_evaluator.cli score $(pwd)/data/parsed --role "Designer"

# Or use --sample flag for testing
python -m jd_fit_evaluator.cli score --sample --role "Designer"
```

#### Performance Issues

**Slow embedding generation**

```bash
# Switch to mock provider for testing
export JD_FIT_EMBEDDINGS__PROVIDER=mock

# Or reduce batch size
export JD_FIT_EMBEDDINGS__BATCH_SIZE=64
```

**UI not loading**

```bash
# Check port availability
lsof -i :8501

# Use different port
streamlit run ui/app.py --server.port 8502
```

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
export JD_FIT_LOG_LEVEL=DEBUG
python -m jd_fit_evaluator.cli score --sample --role "Designer"
```

### Getting Help

1. Check the [docs/](docs/) directory for additional documentation
2. Review test files in [tests/](tests/) for usage examples
3. Open an issue on GitHub with:
   - Error message and stack trace
   - JD-Fit version (`pip show jd-fit-evaluator`)
   - Python version (`python --version`)
   - Configuration (redact sensitive values)

## Contributing

We welcome contributions! Please follow these guidelines:

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/jd-fit-evaluator.git
cd jd-fit-evaluator

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linting
ruff check src tests
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_scoring_features.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run fast tests only (skip slow integration tests)
pytest -m "not slow"
```

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints for all functions
- Add docstrings for public APIs
- Write tests for new features
- Keep commits atomic and well-described

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Legal & Ethics

### Responsible AI Use

- **Human-in-the-Loop**: JD-Fit is designed as **decision support**, not automated rejection
- **Transparency**: All scores include rationales explaining the reasoning
- **Audit Trail**: Version all scoring weights and keep decision records
- **Bias Monitoring**: Regularly review score distributions across demographics

### Data Privacy

- **Local Processing**: All resume data stays on your infrastructure
- **PII Handling**: Minimize collection and storage of personally identifiable information
- **Access Control**: Restrict access to candidate data based on need-to-know
- **Data Retention**: Implement policies for resume data lifecycle management

### Best Practices

1. **Always review scores manually** before making hiring decisions
2. **Calibrate weights** for your specific role and organization
3. **Monitor for bias** in scoring patterns and outcomes
4. **Document decisions** including overrides of system recommendations
5. **Maintain transparency** with candidates about AI-assisted screening

### Compliance

- Ensure compliance with local employment laws (GDPR, EEOC, etc.)
- Review AI/ML regulations in your jurisdiction
- Consult legal counsel for hiring process requirements
- Maintain documentation for audits and regulatory review

---

**Version**: 0.1.0
**License**: MIT
**Maintainer**: FoundryHR
