#!/bin/bash
# 🚀 JD-Fit Final Run Setup Script
# Optimized setup for 170+ candidate processing

set -e  # Exit on any error

echo "🚀 Setting up JD-Fit Final Run..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

print_error() {
    echo -e "${RED}❌${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ️${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "Please run this script from the jd-fit-evaluator root directory"
    exit 1
fi

print_status "Found jd-fit-evaluator project"

# 1. Activate virtual environment
print_info "Activating virtual environment..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
    print_status "Virtual environment activated"
else
    print_warning "Virtual environment not found, creating one..."
    python -m venv .venv
    source .venv/bin/activate
    print_status "Virtual environment created and activated"
fi

# 2. Install dependencies
print_info "Installing dependencies (including OpenAI)..."
pip install -e .[dev,openai]
print_status "Dependencies installed"

# 3. Install additional optimization packages
print_info "Installing optimization packages..."
pip install rich typer
print_status "Optimization packages installed"

# 4. Set up environment variables
print_info "Checking environment configuration..."

# Check if .env exists
if [ ! -f ".env" ]; then
    print_warning ".env file not found!"
    print_info "Creating .env file from template..."
    cp optimized_config.env .env
    print_warning "IMPORTANT: Edit .env file and add your OpenAI API key!"
    print_warning "Set OPENAI_API_KEY=sk-your-actual-key-here"
    exit 1
else
    print_status ".env file exists"

    # Check if OPENAI_API_KEY is set in .env
    if grep -q "^OPENAI_API_KEY=sk-" .env; then
        print_status "OpenAI API key is configured in .env"
    else
        print_warning "OpenAI API key not found in .env file"
        print_warning "Please add: OPENAI_API_KEY=sk-your-actual-key-here"
    fi
fi

# 5. Set OpenAI environment variables for this session
if [ -n "$OPENAI_API_KEY" ]; then
    export JD_FIT_EMBEDDINGS__PROVIDER=openai
    export JD_FIT_EMBEDDINGS__MODEL=text-embedding-3-small
    export JD_FIT_EMBEDDINGS__BATCH_SIZE=256
    print_status "OpenAI configuration set for this session"
else
    print_warning "OPENAI_API_KEY not set - will use mock embeddings"
    export JD_FIT_EMBEDDINGS__PROVIDER=mock
fi

# 6. Create necessary directories
print_info "Creating output directories..."
mkdir -p out
mkdir -p data/candidates
mkdir -p .cache
print_status "Directories created"

# 7. Check candidates folder
print_info "Checking candidates folder..."
if [ -d "$HOME/Desktop/Candidates" ]; then
    CANDIDATE_COUNT=$(find "$HOME/Desktop/Candidates" -name "*.pdf" | wc -l)
    print_status "Found $CANDIDATE_COUNT candidates in ~/Desktop/Candidates"
else
    print_error "Candidates folder not found at ~/Desktop/Candidates"
    print_info "Please ensure your 170+ candidate PDFs are in ~/Desktop/Candidates"
    exit 1
fi

# 8. Run health check
print_info "Running health check..."
python optimized_final_run.py health-check

# 9. Check if candidates are parsed
if [ -d "data/candidates" ]; then
    PARSED_COUNT=$(find "data/candidates" -name "*.json" | wc -l)
    if [ $PARSED_COUNT -gt 0 ]; then
        print_status "Found $PARSED_COUNT parsed candidates in data/candidates"

        # Create manifest if it doesn't exist
        if [ ! -f "data/manifest.json" ]; then
            print_info "Creating manifest from parsed candidates..."
            python optimized_final_run.py create-manifest \
                "data/candidates" \
                --manifest "data/manifest.json"
            print_status "Manifest created"
        else
            print_status "Manifest already exists"
        fi
    else
        print_warning "No parsed candidates found in data/candidates"
        print_info "You'll need to parse candidates first or use run-from-folder command"
    fi
else
    print_warning "data/candidates folder not found"
    print_info "You can use run-from-folder command to score without a manifest"
fi

# 10. Check if Agoric profile exists
print_info "Checking job profile..."
if [ -f "data/profiles/AGORIC_SENIOR_PRODUCT_DESIGNER.json" ]; then
    print_status "Agoric profile found"
else
    print_warning "Agoric profile not found, will use built-in profile"
fi

print_status "Setup complete!"
echo ""
echo "🎯 Ready to run optimized final scoring:"
echo ""
echo "Method 1 - With manifest (if you have data/manifest.json):"
echo "   python optimized_final_run.py run-optimized \\"
echo "     data/manifest.json \\"
echo "     data/profiles/AGORIC_SENIOR_PRODUCT_DESIGNER.json \\"
echo "     --workers 8 \\"
echo "     --batch-size 32 \\"
echo "     --out out"
echo ""
echo "Method 2 - Direct from folder (no manifest needed):"
echo "   python optimized_final_run.py run-from-folder \\"
echo "     data/candidates \\"
echo "     data/profiles/AGORIC_SENIOR_PRODUCT_DESIGNER.json \\"
echo "     --workers 8 \\"
echo "     --batch-size 32 \\"
echo "     --out out"
echo ""
echo "📊 Monitor progress with:"
echo "   tail -f out/batch_summary.md"
echo ""
echo "🌐 Launch UI with:"
echo "   make ui"
echo "   # Then open http://localhost:8501"
