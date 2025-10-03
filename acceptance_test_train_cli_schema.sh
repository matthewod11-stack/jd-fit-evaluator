#!/bin/bash
set -euo pipefail
source .venv/bin/activate || python -m venv .venv && source .venv/bin/activate

# 1) Score writes both candidate_id and name_norm
python - <<'PY'
from jd_fit_evaluator.cli import score
score('data/sample/jd.txt', sample=True)
PY

python - <<'PY'
import json, sys
d=json.load(open("data/out/scores.json"))
results = d.get("results", [])
if not results:
    print("No results found in scores.json")
    sys.exit(1)
row = results[0]
assert "candidate_id" in row and row["candidate_id"], "missing candidate_id"
assert "name_norm" in row, "missing name_norm"
print("✓ schema contains candidate_id and name_norm")
PY

# 2) Train does not crash when labels missing; exits 0 with guidance
python - <<'PY'
try:
    from jd_fit_evaluator.cli import train_impl
    train_impl()  # Should handle missing labels gracefully
    print("✓ train completed without crash")
except SystemExit as e:
    if e.code == 0:
        print("✓ train exited gracefully with code 0")
    else:
        print(f"✗ train exited with code {e.code}")
        raise
except Exception as e:
    print(f"✗ train crashed with exception: {e}")
    raise
PY

# 3) UI reads new keys and sorts by fit (manual smoke): start Streamlit and load table
# streamlit run ui/app.py