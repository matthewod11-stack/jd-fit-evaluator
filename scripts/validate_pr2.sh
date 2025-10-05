#!/bin/bash
"""
Final validation script for PR2 - ETL consolidation.
Comprehensive verification that all ETL modules are unified and working.
"""

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== PR2 ETL Consolidation Validation ==="

# Function to print status
print_status() {
    if [ $1 -eq 0 ]; then
        echo "✅ $2"
    else
        echo "❌ $2"
        return 1
    fi
}

ERRORS=0

# 1. Verify legacy directory is gone
echo "1. Checking legacy directory removal..."
if [ -d "src/etl" ]; then
    echo "❌ Legacy src/etl directory still exists"
    ((ERRORS++))
else
    echo "✅ Legacy src/etl directory removed"
fi

# 2. Verify current ETL structure
echo "2. Checking current ETL structure..."
REQUIRED_FILES=(
    "src/jd_fit_evaluator/etl/__init__.py"
    "src/jd_fit_evaluator/etl/manifest_schema.py"
    "src/jd_fit_evaluator/etl/manifest_ingest.py"
    "src/jd_fit_evaluator/etl/ingestion.py"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        ((ERRORS++))
    fi
done

# 3. Check for legacy imports
echo "3. Checking for legacy imports..."
LEGACY_IMPORTS=$(grep -r "from src\.etl" --include="*.py" . 2>/dev/null | grep -v "scripts/" | wc -l)
if [ "$LEGACY_IMPORTS" -eq 0 ]; then
    echo "✅ No legacy ETL imports found"
else
    echo "❌ Found $LEGACY_IMPORTS legacy ETL imports"
    grep -r "from src\.etl" --include="*.py" . 2>/dev/null | grep -v "scripts/"
    ((ERRORS++))
fi

# 4. Test Python imports
echo "4. Testing Python imports..."
python3 -c "
import sys
sys.path.insert(0, 'src')
success = True
try:
    from jd_fit_evaluator.etl.manifest_schema import coerce_row, ManifestRow, Manifest
    print('✅ manifest_schema imports work')
except ImportError as e:
    print(f'❌ manifest_schema import error: {e}')
    success = False

try:
    from jd_fit_evaluator.etl.manifest_ingest import read_manifest, ingest_manifest_rows
    print('✅ manifest_ingest imports work')
except ImportError as e:
    print(f'❌ manifest_ingest import error: {e}')
    success = False

try:
    from jd_fit_evaluator.etl.ingestion import ingest_manifest_rows as alt_ingest
    print('✅ ingestion imports work')
except ImportError as e:
    print(f'❌ ingestion import error: {e}')
    success = False

if not success:
    exit(1)
"
if [ $? -ne 0 ]; then
    ((ERRORS++))
fi

# 5. Run unified tests
echo "5. Running ETL tests..."
if python -m pytest tests/test_etl_unified.py -v >/dev/null 2>&1; then
    echo "✅ Unified ETL tests pass"
else
    echo "❌ Unified ETL tests failed"
    ((ERRORS++))
fi

# 6. Run existing ETL tests
echo "6. Running existing ETL tests..."
if python -m pytest tests/ -k "etl or manifest" -v >/dev/null 2>&1; then
    echo "✅ All ETL-related tests pass"
else
    echo "❌ Some ETL tests failed"
    ((ERRORS++))
fi

# 7. Test coerce_row functionality specifically
echo "7. Testing coerce_row function..."
python3 -c "
import sys, tempfile
sys.path.insert(0, 'src')
from jd_fit_evaluator.etl.manifest_schema import coerce_row

# Create test file
with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
    tmp.write(b'%PDF test')
    test_file = tmp.name

try:
    # Test basic functionality
    result = coerce_row({'candidate_id': 'test', 'source_path': test_file})
    print('✅ coerce_row basic functionality works')
    
    # Test legacy field mapping
    result = coerce_row({'candidate_id': 'test2', 'resume_path': test_file})
    assert result.source_path == test_file
    print('✅ coerce_row legacy field mapping works')
    
except Exception as e:
    print(f'❌ coerce_row test failed: {e}')
    exit(1)
finally:
    import os
    os.unlink(test_file)
"
if [ $? -ne 0 ]; then
    ((ERRORS++))
fi

echo ""
echo "=== Validation Summary ==="
if [ $ERRORS -eq 0 ]; then
    echo "🎉 All validations passed!"
    echo "PR2 ETL consolidation is complete and working correctly."
    echo ""
    echo "Key achievements:"
    echo "  - Legacy src/etl directory removed"
    echo "  - Single source of truth in src/jd_fit_evaluator/etl/"
    echo "  - All imports unified and working"
    echo "  - Tests pass with consolidated modules"
    echo "  - coerce_row function has robust implementation"
    exit 0
else
    echo "❌ $ERRORS validation errors found"
    echo "ETL consolidation needs attention before PR completion."
    exit 1
fi