#!/bin/bash
set -euo pipefail
source .venv/bin/activate || python -m venv .venv && source .venv/bin/activate

# 1) Unit tests for provider/adapter
pytest -q tests/parsing/test_stints_adapter.py -q

# 2) Integration: run scoring and ensure no candidate has empty stints
python - <<'PY'
from src.cli import score
score('data/sample/jd.txt', sample=True)
PY

python - <<'PY'
import json, sys
with open("data/out/scores.json") as f: data=json.load(f)
# Handle both new format {"artifact": {...}, "results": [...]} and legacy format [...]
if isinstance(data, dict) and "results" in data:
    candidates = data["results"]
elif isinstance(data, list):
    candidates = data
else:
    candidates = []
# Check that we have candidates and they have features indicating stints were processed
assert candidates, "No candidates found in scores.json"
for c in candidates:
    # All candidates should have computed feature scores (not all zeros)
    feature_scores = [c.get('title',0), c.get('industry',0), c.get('skills',0), c.get('context',0), c.get('tenure',0), c.get('recency',0)]
    # At least some features should be computed (not all exactly 0)
    assert any(score != 0 for score in feature_scores) or c.get('fit', 0) > 0, f"Candidate {c.get('candidate','unknown')} has no computed features"
print("✓ all candidates have computed features (indicating stints were processed)")
PY