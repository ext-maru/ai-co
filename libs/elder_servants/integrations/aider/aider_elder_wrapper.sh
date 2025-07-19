#!/bin/bash
# Aider wrapper script with Elder Servants integration

# Elder Servants Aider Wrapper
# This script wraps aider to automatically integrate with Elder Servants

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 Aider + Elder Servants Integration${NC}"
echo -e "${BLUE}=====================================\=${NC}"

# Check if aider is installed
if ! command -v aider &> /dev/null; then
    echo -e "${RED}❌ Aider is not installed!${NC}"
    echo -e "${YELLOW}Install with: pip install aider-chat${NC}"
    exit 1
fi

# Export Elder integration environment variables
export AIDER_ELDER_INTEGRATION=1
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# Function to setup git hooks
setup_hooks() {
    echo -e "${YELLOW}🔧 Setting up Git hooks for quality checks...${NC}"
    
    # Get git directory
    GIT_DIR=$(git rev-parse --git-dir 2>/dev/null)
    if [ -z "$GIT_DIR" ]; then
        echo -e "${RED}❌ Not in a git repository${NC}"
        return 1
    fi
    
    # Create hooks directory if it doesn't exist
    mkdir -p "$GIT_DIR/hooks"
    
    # Create pre-commit hook
    cat > "$GIT_DIR/hooks/pre-commit" << 'EOF'
#!/bin/bash
# Elder Servants quality check pre-commit hook

# Get the list of files to be committed
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|js|ts|jsx|tsx)$')

if [ -z "$FILES" ]; then
    exit 0
fi

echo "🗡️ Running Iron Will quality checks..."

# Run Python quality check
python3 -c "
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, '$PROJECT_ROOT')

from libs.elder_servants.integrations.aider.aider_elder_integration import AiderElderIntegration

async def main():
    integration = AiderElderIntegration()
    files = '''$FILES'''.strip().split('\n')
    should_commit, message = await integration.pre_commit_hook(files)
    print(message)
    return 0 if should_commit else 1

sys.exit(asyncio.run(main()))
"

RESULT=$?

if [ $RESULT -ne 0 ]; then
    echo "❌ Commit blocked by Iron Will quality standards"
    echo "💡 Fix the issues or use --no-verify to skip checks"
    exit 1
fi

echo "✅ All quality checks passed!"
exit 0
EOF
    
    chmod +x "$GIT_DIR/hooks/pre-commit"
    echo -e "${GREEN}✅ Git hooks installed${NC}"
}

# Function to run aider with quality monitoring
run_with_monitoring() {
    # Start quality monitoring in background
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '$PROJECT_ROOT')

from libs.elder_servants.integrations.aider.quality_monitor import QualityMonitor

async def monitor():
    monitor = QualityMonitor()
    await monitor.start_monitoring()

try:
    asyncio.run(monitor())
except KeyboardInterrupt:
    pass
" &
    
    MONITOR_PID=$!
    
    # Run aider with all arguments
    aider "$@"
    AIDER_EXIT=$?
    
    # Stop monitor
    kill $MONITOR_PID 2>/dev/null
    
    return $AIDER_EXIT
}

# Parse command line options
SKIP_HOOKS=false
QUALITY_MODE=false
ELDER_ARGS=()
AIDER_ARGS=()

for arg in "$@"; do
    case $arg in
        --skip-hooks)
            SKIP_HOOKS=true
            ;;
        --elder-quality)
            QUALITY_MODE=true
            ;;
        --elder-*)
            ELDER_ARGS+=("$arg")
            ;;
        *)
            AIDER_ARGS+=("$arg")
            ;;
    esac
done

# Setup hooks unless skipped
if [ "$SKIP_HOOKS" = false ]; then
    setup_hooks
fi

# Show integration features
echo -e "${GREEN}🌟 Elder Integration Features:${NC}"
echo "  - Iron Will quality checks (95% standard)"
echo "  - Automatic commit enhancement"
echo "  - Git Keeper Servant integration"
echo "  - Real-time quality monitoring"
echo ""

# Add Elder-specific aider settings
export AIDER_COMMIT_PREFIX="🤖 "
export AIDER_AUTO_COMMITS=true

# If quality mode, add specific prompts
if [ "$QUALITY_MODE" = true ]; then
    echo -e "${YELLOW}📊 Running in Elder Quality Mode${NC}"
    export AIDER_EDITOR_MODEL="claude-3-5-sonnet-20241022"
    export AIDER_EDITOR_EDIT_FORMAT="diff"
    
    # Add quality prompt
    QUALITY_PROMPT="Always ensure code meets these Iron Will standards:
- Test coverage must be above 80%
- No security vulnerabilities
- Follow PEP8/ESLint standards
- Include proper error handling
- Add comprehensive docstrings/comments
"
    
    # Run with quality prompt
    echo "$QUALITY_PROMPT" | run_with_monitoring "${AIDER_ARGS[@]}"
else
    # Normal run
    run_with_monitoring "${AIDER_ARGS[@]}"
fi

echo -e "${BLUE}👋 Elder Servants signing off${NC}"