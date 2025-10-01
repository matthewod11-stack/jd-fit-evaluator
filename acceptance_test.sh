#!/bin/bash
set -euo pipefail

# 0) Env
export EMBED_BACKEND=ollama
export EMBED_MODEL=nomic-embed-text
export EMBED_DIM=768
export DRY_RUN=true
[ -d .venv ] || python -m venv .venv
source .venv/bin/activate || true
python - <<'PY'
import importlib, subprocess, sys
for dep in ["pytest","typer","requests","numpy"]:
    try: importlib.import_module(dep)
    except ImportError: subprocess.check_call([sys.executable,"-m","pip","install",dep])
PY

# 1) Unit tests
pytest -q tests/models/test_embeddings.py -q

# 2) Sample score run should NOT throw and should log 768-d vectors
python -m src.cli score --jd data/jd.txt --sample

# 3) Artifact sanity: verify out/scores.json exists
test -f out/scores.json && echo "✓ scores.json written"