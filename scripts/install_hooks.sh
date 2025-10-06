#!/bin/bash

# Git Hooks Installation Script
# This script installs pre-commit hooks to enforce code quality standards

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOKS_DIR="$PROJECT_ROOT/.git/hooks"

echo "🔧 Installing JD-Fit Evaluator pre-commit hooks..."

# Ensure hooks directory exists
mkdir -p "$HOOKS_DIR"

# Create pre-commit hook
cat > "$HOOKS_DIR/pre-commit" << 'EOF'
#!/bin/bash

# JD-Fit Evaluator Pre-commit Hook
# Enforces code quality standards before commits

set -e

echo "🔍 Running pre-commit checks..."

# Change to project root
cd "$(git rev-parse --show-toplevel)"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check 1: Import pattern validation
echo "  ✓ Checking import patterns..."
if ! make guardpaths > /dev/null 2>&1; then
    echo "❌ Import pattern violations detected!"
    echo "   Run 'make guardpaths' to see details"
    echo "   Fix import violations before committing"
    exit 1
fi

# Check 2: Test suite
echo "  ✓ Running test suite..."
if ! pytest --tb=short -q > /dev/null 2>&1; then
    echo "❌ Test failures detected!"
    echo "   Run 'pytest -v' to see details"
    echo "   Fix failing tests before committing"
    exit 1
fi

# Check 3: Code linting
echo "  ✓ Running linter..."
if ! ruff check > /dev/null 2>&1; then
    echo "❌ Linting violations detected!"
    echo "   Run 'ruff check' to see details"
    echo "   Fix linting issues before committing"
    exit 1
fi

echo "✅ All pre-commit checks passed!"
EOF

# Make pre-commit hook executable
chmod +x "$HOOKS_DIR/pre-commit"

# Verify hook installation
if [ -x "$HOOKS_DIR/pre-commit" ]; then
    echo "✅ Pre-commit hook installed successfully"
    echo "   Location: $HOOKS_DIR/pre-commit"
    echo ""
    echo "🎯 The hook will now run automatically before each commit and will:"
    echo "   • Check for import pattern violations (make guardpaths)"
    echo "   • Run the test suite (pytest)"
    echo "   • Check code style (ruff check)"
    echo ""
    echo "💡 To bypass the hook temporarily (not recommended):"
    echo "   git commit --no-verify -m \"message\""
    echo ""
    echo "🧪 To test the hook manually:"
    echo "   .git/hooks/pre-commit"
else
    echo "❌ Failed to install pre-commit hook"
    exit 1
fi

echo "🔧 Hook installation complete!"