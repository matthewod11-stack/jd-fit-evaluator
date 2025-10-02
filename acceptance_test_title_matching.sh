#!/bin/bash
set -euo pipefail
source .venv/bin/activate || python -m venv .venv && source .venv/bin/activate

# 1) Unit tests for title matching
pytest -q tests/scoring/test_title_match.py -q

# 2) Sample run should raise titles_subscore for obvious matches
python -m src.cli score data/jd.txt --sample

# 3) Spot-check: parse out two sample candidates and print their title subscore
python - <<'PY'
import json, re
with open("out/scores.json") as f: data=json.load(f)
def find_sub(c):
    return c.get("subs",{}).get("titles") or c.get("features",{}).get("titles_subscore")
samples=data.get("candidates",[])[:5]
for c in samples:
    print(c.get("candidate_id", c.get("candidate")), find_sub(c))
PY
