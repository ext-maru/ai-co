#!/bin/bash
# Setup script for ai-git tool

set -e

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AI_GIT_PATH="$SCRIPT_DIR/scripts/ai-git"

echo "Setting up ai-git tool..."

# Make ai-git executable
if [[ -f "$AI_GIT_PATH" ]]; then
    chmod +x "$AI_GIT_PATH"
    echo "✅ ai-git script made executable"
else
    echo "❌ ai-git script not found at $AI_GIT_PATH"
    exit 1
fi

# Check if git is configured
if ! git config user.name > /dev/null 2>&1; then
    echo "⚠️  Git user.name is not configured"
    echo "   Run: git config --global user.name 'Your Name'"
fi

if ! git config user.email > /dev/null 2>&1; then
    echo "⚠️  Git user.email is not configured"
    echo "   Run: git config --global user.email 'your.email@example.com'"
fi

# Check if GitHub CLI is available
if ! command -v gh > /dev/null 2>&1; then
    echo "⚠️  GitHub CLI (gh) is not installed"
    echo "   Install from: https://cli.github.com/"
    echo "   Or use manual PR creation mode"
fi

# Check Python environment
if [[ -f "$SCRIPT_DIR/venv/bin/activate" ]]; then
    echo "✅ Python virtual environment found"

    # Check if AI assistant module is available
    source "$SCRIPT_DIR/venv/bin/activate"
    if python3 -c "import sys; sys.path.append('$SCRIPT_DIR'); from libs.ai_git_assistant import AIGitAssistant; print('AI support available')" 2>/dev/null; then
        echo "✅ AI Git Assistant module available"
    else
        echo "⚠️  AI Git Assistant module not available"
        echo "   AI features will be disabled"
    fi
else
    echo "⚠️  Python virtual environment not found at $SCRIPT_DIR/venv"
    echo "   AI features will be disabled"
fi

# Add to PATH if not already there
if ! echo "$PATH" | grep -q "$SCRIPT_DIR/scripts"; then
    echo "📝 To use ai-git from anywhere, add to your PATH:"
    echo "   export PATH=\"$SCRIPT_DIR/scripts:\$PATH\""
    echo "   Or add this line to your ~/.bashrc or ~/.zshrc"
fi

echo
echo "🎉 ai-git setup complete!"
echo
echo "Usage examples:"
echo "  $AI_GIT_PATH feature user-auth"
echo "  $AI_GIT_PATH pr 'Add user authentication'"
echo "  $AI_GIT_PATH status"
echo "  $AI_GIT_PATH help"
