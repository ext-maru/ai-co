#!/bin/bash
# 🛑 Quality Servants 停止スクリプト

set -e

echo "🛑 Stopping Quality Pipeline Servants..."

# 色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# PIDファイルから読み込み
if [ -f /tmp/quality_watcher.pid ]; then
    QUALITY_WATCHER_PID=$(cat /tmp/quality_watcher.pid)
    if kill -0 $QUALITY_WATCHER_PID 2>/dev/null; then
        kill $QUALITY_WATCHER_PID
        echo -e "${GREEN}✅ QualityWatcher stopped (PID: $QUALITY_WATCHER_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️ QualityWatcher not running${NC}"
    fi
    rm -f /tmp/quality_watcher.pid
else
    echo -e "${YELLOW}⚠️ QualityWatcher PID file not found${NC}"
fi

if [ -f /tmp/test_forge.pid ]; then
    TEST_FORGE_PID=$(cat /tmp/test_forge.pid)
    if kill -0 $TEST_FORGE_PID 2>/dev/null; then
        kill $TEST_FORGE_PID
        echo -e "${GREEN}✅ TestForge stopped (PID: $TEST_FORGE_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️ TestForge not running${NC}"
    fi
    rm -f /tmp/test_forge.pid
else
    echo -e "${YELLOW}⚠️ TestForge PID file not found${NC}"
fi

if [ -f /tmp/comprehensive_guardian.pid ]; then
    COMPREHENSIVE_GUARDIAN_PID=$(cat /tmp/comprehensive_guardian.pid)
    if kill -0 $COMPREHENSIVE_GUARDIAN_PID 2>/dev/null; then
        kill $COMPREHENSIVE_GUARDIAN_PID
        echo -e "${GREEN}✅ ComprehensiveGuardian stopped (PID: $COMPREHENSIVE_GUARDIAN_PID)${NC}"
    else
        echo -e "${YELLOW}⚠️ ComprehensiveGuardian not running${NC}"
    fi
    rm -f /tmp/comprehensive_guardian.pid
else
    echo -e "${YELLOW}⚠️ ComprehensiveGuardian PID file not found${NC}"
fi

# プロセス名でも検索して確実に停止
echo -e "${YELLOW}🔍 Checking for remaining processes...${NC}"
pkill -f "quality_watcher_servant" 2>/dev/null || true
pkill -f "test_forge_servant" 2>/dev/null || true
pkill -f "comprehensive_guardian_servant" 2>/dev/null || true

echo -e "${GREEN}✅ All Quality Servants stopped${NC}"