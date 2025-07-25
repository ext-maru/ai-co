#!/bin/bash
# 🚀 Quality Servants 起動スクリプト
# 3つのサーバントを順次起動

set -e

echo "🏛️ Starting Quality Pipeline Servants..."

# 色定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# プロジェクトルート
PROJECT_ROOT="/home/aicompany/ai_co"
cd "$PROJECT_ROOT"

# Python環境確認
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi

# 仮想環境アクティベート（存在する場合）
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
fi

# 各サーバントを別プロセスで起動
echo -e "${YELLOW}🧝‍♂️ Starting QualityWatcher Servant (Port 8810)...${NC}"
python3 -m elders_guild.quality_servants.quality_watcher_servant &
QUALITY_WATCHER_PID=$!
echo "PID: $QUALITY_WATCHER_PID"
sleep 2

echo -e "${YELLOW}🔨 Starting TestForge Servant (Port 8811)...${NC}"
python3 -m elders_guild.quality_servants.test_forge_servant &
TEST_FORGE_PID=$!
echo "PID: $TEST_FORGE_PID"
sleep 2

echo -e "${YELLOW}🛡️ Starting ComprehensiveGuardian Servant (Port 8812)...${NC}"
python3 -m elders_guild.quality_servants.comprehensive_guardian_servant &
COMPREHENSIVE_GUARDIAN_PID=$!
echo "PID: $COMPREHENSIVE_GUARDIAN_PID"
sleep 2

# PIDファイル作成
echo "$QUALITY_WATCHER_PID" > /tmp/quality_watcher.pid
echo "$TEST_FORGE_PID" > /tmp/test_forge.pid
echo "$COMPREHENSIVE_GUARDIAN_PID" > /tmp/comprehensive_guardian.pid

echo -e "${GREEN}✅ All servants started successfully!${NC}"
echo ""
echo "📊 Servant Status:"
echo "  - QualityWatcher: http://localhost:8810 (PID: $QUALITY_WATCHER_PID)"
echo "  - TestForge: http://localhost:8811 (PID: $TEST_FORGE_PID)"
echo "  - ComprehensiveGuardian: http://localhost:8812 (PID: $COMPREHENSIVE_GUARDIAN_PID)"
echo ""
echo "💡 To stop servants, run: ./scripts/stop-quality-servants.sh"
echo ""

# ヘルスチェック（オプション）
echo -e "${YELLOW}🏥 Checking servants health...${NC}"
sleep 3

# オーケストレータでヘルスチェック
python3 -m elders_guild.quality.quality_pipeline_orchestrator health || echo -e "${YELLOW}⚠️ Health check requires python-a2a server implementation${NC}"

echo ""
echo -e "${GREEN}🎉 Quality Pipeline System Ready!${NC}"
echo "Run quality check: python3 -m elders_guild.quality.quality_pipeline_orchestrator run --path /path/to/project"

# Ctrl+Cで終了時にサーバントも停止
trap 'echo -e "\n${YELLOW}Stopping servants...${NC}"; kill $QUALITY_WATCHER_PID $TEST_FORGE_PID $COMPREHENSIVE_GUARDIAN_PID 2>/dev/null; exit' INT

# 待機
wait