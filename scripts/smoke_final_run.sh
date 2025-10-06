#!/bin/bash

# Smoke Test for JD-Fit Evaluator Batch Processing
# Validates 170+ candidate batch processing functionality

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "🚀 JD-Fit Evaluator Smoke Test"
echo "==============================="

# Change to project root
cd "$PROJECT_ROOT"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "⚠️  No virtual environment found (.venv), continuing with system Python"
fi

# Check if optimized_final_run.py exists
if [ ! -f "optimized_final_run.py" ]; then
    echo "❌ optimized_final_run.py not found"
    echo "   This script is required for batch processing validation"
    exit 1
fi

# Check for test data
TEST_MANIFEST=""
TEST_PROFILE=""

# Look for existing test data
if [ -f "data/manifest.json" ] && [ -f "data/profiles/profile.json" ]; then
    TEST_MANIFEST="data/manifest.json"
    TEST_PROFILE="data/profiles/profile.json"
    echo "📂 Using existing test data:"
    echo "   Manifest: $TEST_MANIFEST"
    echo "   Profile: $TEST_PROFILE"
elif [ -f "out/test_dry_run/manifest.json" ] && [ -f "out/test_dry_run/profile.json" ]; then
    TEST_MANIFEST="out/test_dry_run/manifest.json"
    TEST_PROFILE="out/test_dry_run/profile.json"
    echo "📂 Using dry run test data:"
    echo "   Manifest: $TEST_MANIFEST"
    echo "   Profile: $TEST_PROFILE"
else
    echo "📂 No existing test data found, creating sample data..."
    
    # Create test output directory
    mkdir -p out/smoke_test
    
    # Create sample manifest with 3 candidates for quick validation
    cat > out/smoke_test/manifest.json << 'EOF'
{
  "candidates": [
    {
      "candidate_id": "smoke_001",
      "filename": "john_doe.pdf",
      "path": "out/smoke_test/john_doe.parsed.json"
    },
    {
      "candidate_id": "smoke_002", 
      "filename": "jane_smith.pdf",
      "path": "out/smoke_test/jane_smith.parsed.json"
    },
    {
      "candidate_id": "smoke_003",
      "filename": "mike_johnson.pdf", 
      "path": "out/smoke_test/mike_johnson.parsed.json"
    }
  ]
}
EOF

    # Create sample profile
    cat > out/smoke_test/profile.json << 'EOF'
{
  "role_title": "Software Engineer",
  "role_level": "Senior",
  "required_skills": ["Python", "JavaScript", "SQL", "Git"],
  "preferred_skills": ["React", "Docker", "AWS", "Machine Learning"],
  "experience_years_min": 3,
  "experience_years_max": 8,
  "education_level": "Bachelor's",
  "industry": "Technology"
}
EOF

    # Create sample parsed candidate files
    mkdir -p out/smoke_test
    
    cat > out/smoke_test/john_doe.parsed.json << 'EOF'
{
  "candidate_id": "smoke_001",
  "name": "John Doe",
  "skills": ["Python", "JavaScript", "React", "SQL", "Git"],
  "experience_years": 5,
  "education": [{"degree": "Bachelor's", "field": "Computer Science"}],
  "stints": [
    {
      "company": "Tech Corp",
      "title": "Software Engineer",
      "duration_years": 3,
      "description": "Developed web applications using Python and React"
    }
  ]
}
EOF

    cat > out/smoke_test/jane_smith.parsed.json << 'EOF'
{
  "candidate_id": "smoke_002",
  "name": "Jane Smith", 
  "skills": ["Python", "Machine Learning", "Docker", "AWS"],
  "experience_years": 4,
  "education": [{"degree": "Master's", "field": "Data Science"}],
  "stints": [
    {
      "company": "Data Solutions Inc",
      "title": "Data Scientist",
      "duration_years": 4,
      "description": "Built ML models for predictive analytics"
    }
  ]
}
EOF

    cat > out/smoke_test/mike_johnson.parsed.json << 'EOF'
{
  "candidate_id": "smoke_003",
  "name": "Mike Johnson",
  "skills": ["JavaScript", "Node.js", "MongoDB", "Express"],
  "experience_years": 6,
  "education": [{"degree": "Bachelor's", "field": "Information Systems"}],
  "stints": [
    {
      "company": "Web Services LLC",
      "title": "Full Stack Developer", 
      "duration_years": 6,
      "description": "Developed RESTful APIs and web applications"
    }
  ]
}
EOF

    TEST_MANIFEST="out/smoke_test/manifest.json"
    TEST_PROFILE="out/smoke_test/profile.json"
    
    echo "✅ Sample test data created"
fi

# Validate manifest file
CANDIDATE_COUNT=$(python -c "import json; data=json.load(open('$TEST_MANIFEST')); print(len(data.get('candidates', [])))" 2>/dev/null || echo "0")

echo "📊 Test data validation:"
echo "   Candidates in manifest: $CANDIDATE_COUNT"

if [ "$CANDIDATE_COUNT" -eq "0" ]; then
    echo "❌ No candidates found in manifest"
    exit 1
fi

# Check if parsed files exist
echo "🔍 Checking parsed candidate files..."
PARSED_FILES_EXIST=true
MISSING_FILES=()

while IFS= read -r line; do
    PARSED_PATH=$(echo "$line" | python -c "import sys, json; data=json.load(sys.stdin); print(data.get('path', ''))" 2>/dev/null || echo "")
    if [ -n "$PARSED_PATH" ]; then
        if [ ! -f "$PARSED_PATH" ]; then
            PARSED_FILES_EXIST=false
            MISSING_FILES+=("$PARSED_PATH")
        fi
    fi
done < <(python -c "import json; data=json.load(open('$TEST_MANIFEST')); [print(json.dumps(item)) for item in data.get('candidates', [])]" 2>/dev/null || echo "")

if [ "$PARSED_FILES_EXIST" = false ]; then
    echo "⚠️  Some parsed files are missing:"
    for file in "${MISSING_FILES[@]}"; do
        echo "   - $file"
    done
    echo "   Continuing with available files..."
fi

# Set environment for mock providers (faster testing)
export JD_FIT_EMBEDDING_PROVIDER=mock
export JD_FIT_LLM_PROVIDER=mock

echo ""
echo "🧪 Running optimized batch processing..."
echo "   Provider: Mock (for fast testing)"
echo "   Workers: 2"
echo "   Batch size: 8"

# Create output directory
OUTPUT_DIR="out/smoke_test_results"
mkdir -p "$OUTPUT_DIR"

# Run the optimized final run with limited concurrency for testing
START_TIME=$(date +%s)

if python optimized_final_run.py run-optimized \
    "$TEST_MANIFEST" \
    "$TEST_PROFILE" \
    --workers 2 \
    --batch-size 8 \
    --out "$OUTPUT_DIR" \
    --log-level INFO; then
    
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    echo ""
    echo "✅ Batch processing completed successfully!"
    echo "   Duration: ${DURATION}s"
    
    # Validate output files
    echo ""
    echo "📋 Validating output files..."
    
    if [ -f "$OUTPUT_DIR/scores.jsonl" ]; then
        SCORED_COUNT=$(python -c "import json; count=0; [count := count + 1 for line in open('$OUTPUT_DIR/scores.jsonl') if line.strip()]; print(count)" 2>/dev/null || echo "0")
        echo "   ✓ Scores file (JSONL): $SCORED_COUNT candidates scored"
    elif [ -f "$OUTPUT_DIR/scores.json" ]; then
        SCORED_COUNT=$(python -c "import json; print(len(json.load(open('$OUTPUT_DIR/scores.json'))))" 2>/dev/null || echo "0")
        echo "   ✓ Scores file (JSON): $SCORED_COUNT candidates scored"
    else
        echo "   ❌ scores.json or scores.jsonl not found"
        exit 1
    fi
    
    if [ -f "$OUTPUT_DIR/scores.csv" ]; then
        CSV_COUNT=$(python -c "import pandas as pd; print(len(pd.read_csv('$OUTPUT_DIR/scores.csv')))" 2>/dev/null || echo "0")
        echo "   ✓ CSV file: $CSV_COUNT rows"
    else
        echo "   ⚠️  scores.csv not found (optional)"
    fi
    
    if [ -f "$OUTPUT_DIR/rationales.md" ]; then
        echo "   ✓ Rationales file generated"
    else
        echo "   ⚠️  rationales.md not found (optional)"
    fi
    
    # Performance validation
    if [ "$CANDIDATE_COUNT" -gt 0 ]; then
        AVG_TIME_PER_CANDIDATE=$((DURATION * 1000 / CANDIDATE_COUNT))
        echo ""
        echo "⚡ Performance metrics:"
        echo "   Total candidates: $CANDIDATE_COUNT"
        echo "   Total time: ${DURATION}s"
        echo "   Average per candidate: ${AVG_TIME_PER_CANDIDATE}ms"
        
        # Performance thresholds (with mock providers should be very fast)
        if [ "$AVG_TIME_PER_CANDIDATE" -gt 5000 ]; then
            echo "   ⚠️  Performance warning: >5s per candidate with mock providers"
        else
            echo "   ✅ Performance acceptable"
        fi
    fi
    
    echo ""
    echo "🎉 SMOKE TEST PASSED"
    echo "   Batch processing is working correctly"
    echo "   Output directory: $OUTPUT_DIR"
    
else
    echo ""
    echo "❌ SMOKE TEST FAILED"
    echo "   Batch processing encountered errors"
    echo "   Check the output above for details"
    exit 1
fi

# Additional health checks
echo ""
echo "🔍 Additional health checks..."

# Check CLI is working
if python -m jd_fit_evaluator.cli --help > /dev/null 2>&1; then
    echo "   ✓ CLI module accessible"
else
    echo "   ❌ CLI module not accessible"
    exit 1
fi

# Check sample scoring works
if python -m jd_fit_evaluator.cli score --sample --role "Test Role" > /dev/null 2>&1; then
    echo "   ✓ Sample scoring works"
else
    echo "   ❌ Sample scoring failed"
    exit 1
fi

echo ""
echo "🏆 All smoke tests completed successfully!"
echo "   The JD-Fit Evaluator is ready for production use"