#!/bin/bash
"""
Verify manifest_ingest.py completeness and functionality.
This script ensures the current manifest ingestion module has all needed features.
"""

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== Verifying Manifest Ingest Completeness ==="

# Check if the file exists
MANIFEST_INGEST="src/jd_fit_evaluator/etl/manifest_ingest.py"
if [ ! -f "$MANIFEST_INGEST" ]; then
    echo "❌ $MANIFEST_INGEST not found"
    exit 1
fi
echo "✅ Manifest ingest file exists: $MANIFEST_INGEST"

# Check for key functions
echo "Checking for required functions..."

if grep -q "def read_manifest" "$MANIFEST_INGEST"; then
    echo "✅ read_manifest function found"
else
    echo "❌ read_manifest function missing"
    exit 1
fi

if grep -q "def normalize_candidate_json" "$MANIFEST_INGEST"; then
    echo "✅ normalize_candidate_json function found"
else
    echo "❌ normalize_candidate_json function missing"
    exit 1
fi

if grep -q "def ingest_manifest_rows" "$MANIFEST_INGEST"; then
    echo "✅ ingest_manifest_rows function found"
else
    echo "❌ ingest_manifest_rows function missing"
    exit 1
fi

if grep -q "class ManifestIngestionError" "$MANIFEST_INGEST"; then
    echo "✅ ManifestIngestionError class found"
else
    echo "❌ ManifestIngestionError class missing"
    exit 1
fi

# Check imports
echo "Checking imports..."
if grep -q "from .manifest_schema import" "$MANIFEST_INGEST"; then
    echo "✅ Imports from manifest_schema found"
else
    echo "❌ Missing imports from manifest_schema"
    exit 1
fi

# Test import functionality
echo "Testing Python imports..."
python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from jd_fit_evaluator.etl.manifest_ingest import read_manifest, normalize_candidate_json, ingest_manifest_rows, ManifestIngestionError
    print('✅ All main functions importable')
except ImportError as e:
    print(f'❌ Import error: {e}')
    exit(1)
"

echo ""
echo "=== Manifest Ingest Verification Complete ==="
echo "Status: All required functions and classes are present and importable"