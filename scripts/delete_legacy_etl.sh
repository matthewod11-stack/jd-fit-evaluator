#!/bin/bash
"""
Safe deletion script for legacy ETL directory with comprehensive checks.
Only deletes if all verification passes.
"""

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Safe Legacy ETL Deletion Script ==="

LEGACY_ETL_DIR="src/etl"

# Check if legacy directory exists
if [ ! -d "$LEGACY_ETL_DIR" ]; then
    echo "✅ Legacy ETL directory already removed: $LEGACY_ETL_DIR"
    exit 0
fi

echo "⚠️  Legacy ETL directory found: $LEGACY_ETL_DIR"

# Safety checks before deletion
echo "Running safety checks..."

# 1. Verify no imports from legacy location
echo "1. Checking for legacy imports..."
if grep -r "from src\.etl" --include="*.py" src/ tests/ app/ ui/ 2>/dev/null; then
    echo "❌ Found imports from legacy ETL location. Migration incomplete!"
    exit 1
fi
echo "✅ No legacy ETL imports found"

# 2. Verify current ETL directory exists and has content
CURRENT_ETL_DIR="src/jd_fit_evaluator/etl"
if [ ! -d "$CURRENT_ETL_DIR" ]; then
    echo "❌ Current ETL directory missing: $CURRENT_ETL_DIR"
    exit 1
fi

if [ ! -f "$CURRENT_ETL_DIR/manifest_schema.py" ] || [ ! -f "$CURRENT_ETL_DIR/manifest_ingest.py" ]; then
    echo "❌ Current ETL directory missing key files"
    exit 1
fi
echo "✅ Current ETL directory has required files"

# 3. Test that current imports work
echo "3. Testing current ETL imports..."
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from jd_fit_evaluator.etl.manifest_schema import coerce_row
    from jd_fit_evaluator.etl.manifest_ingest import read_manifest
    print('✅ Current ETL imports work')
except ImportError as e:
    print(f'❌ Current ETL import error: {e}')
    exit(1)
"

# 4. Run tests to ensure nothing breaks
echo "4. Running relevant tests..."
if ! python -m pytest tests/test_etl_unified.py -v 2>/dev/null; then
    echo "❌ ETL tests failed - not safe to delete legacy directory"
    exit 1
fi
echo "✅ ETL tests pass"

# All checks passed - safe to delete
echo ""
echo "All safety checks passed. Proceeding with deletion..."

# Move to archive instead of deleting (safer)
ARCHIVE_DIR="archive/legacy_etl_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$ARCHIVE_DIR"
mv "$LEGACY_ETL_DIR" "$ARCHIVE_DIR/"

echo "✅ Legacy ETL directory moved to archive: $ARCHIVE_DIR/etl"
echo ""
echo "=== Legacy ETL Deletion Complete ==="
echo "Status: Legacy directory safely archived, current ETL modules verified"