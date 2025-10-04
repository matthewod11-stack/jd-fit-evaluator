#!/bin/bash
set -e

echo "=== Verifying Legacy Directory Migration ==="

# Check for any remaining references to old structure
echo -e "\n1. Checking for remaining src.* imports..."
if rg "from src\.(scoring|parsing|etl)" --type py; then
    echo "❌ Found legacy imports - migration incomplete"
    exit 1
else
    echo "✅ No legacy src.* imports found"
fi

echo -e "\n2. Checking for bare scoring/parsing imports..."
if rg "^from (scoring|parsing|etl)\." --type py; then
    echo "❌ Found bare imports - migration incomplete"
    exit 1
else
    echo "✅ No bare imports found"
fi

echo -e "\n3. Checking for sys.path.insert in production code..."
# Exclude scripts/, validate_optimization.py, and migration scripts
if rg "sys\.path\.insert" --type py --glob '!scripts/**' --glob '!validate_optimization.py' --glob '!optimized_final_run.py'; then
    echo "❌ Found sys.path hacks in production code - migration incomplete"
    exit 1
else
    echo "✅ No sys.path hacks found in production code"
fi

echo -e "\n4. Verifying new structure has all needed files..."
for dir in scoring parsing etl models utils; do
    if [ ! -d "src/jd_fit_evaluator/$dir" ]; then
        echo "❌ Missing directory: src/jd_fit_evaluator/$dir"
        exit 1
    fi
done
echo "✅ All expected directories present"

echo -e "\n5. Safe to delete legacy directories:"
echo "   - src/scoring/"
echo "   - src/parsing/"
echo "   - src/etl/"

echo -e "\n=== Migration verification complete ==="
