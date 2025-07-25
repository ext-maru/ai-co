#!/bin/bash
# 🔍 自動イシュー処理システム監視スクリプト
# エルダーズギルド評議会承認済み

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"

echo -e "${BLUE}🏛️ エルダーズギルド - 自動イシュー処理システム監視${NC}"
echo -e "${BLUE}================================================${NC}"

# 最新ログファイルを取得
LATEST_LOG=$(ls -t "$LOG_DIR/enhanced_auto_pr/"*.log 2>/dev/null | head -1)
LATEST_TIME=$(basename "$LATEST_LOG" .log | sed 's/.*_//')

echo -e "\n${GREEN}📊 システム状態${NC}"
echo -e "最新実行: $(echo $LATEST_TIME | sed 's/\(..\)\(..\)\(..\)/\1:\2:\3/')"

# 処理統計を表示
echo -e "\n${GREEN}📈 本日の処理統計${NC}"
TODAY=$(date +%Y-%m-%d)
if [ -f "$LOG_DIR/auto_issue_processing.json" ]; then
    TOTAL_PROCESSED=$(grep "$TODAY" "$LOG_DIR/auto_issue_processing.json" | wc -l)
    UNIQUE_ISSUES=$(cat "$LOG_DIR/auto_issue_processing.json" | jq -r ".[] | select(.timestamp | contains(\"$TODAY\")) | .issue_id" 2>/dev/null | sort -u | wc -l)
    echo -e "総処理回数: ${YELLOW}$TOTAL_PROCESSED${NC}"
    echo -e "処理イシュー数: ${YELLOW}$UNIQUE_ISSUES${NC}"
fi

# Elder Flow実行状況
echo -e "\n${GREEN}🌊 Elder Flow実行状況${NC}"
if [ -f "$LOG_DIR/elder_flow_engine.log" ]; then
    ELDER_FLOW_TODAY=$(grep "$TODAY" "$LOG_DIR/elder_flow_engine.log" | grep "Elder Flow実行完了" | wc -l)
    echo -e "本日のElder Flow実行: ${YELLOW}$ELDER_FLOW_TODAY${NC} 回"
fi

# エラー監視
echo -e "\n${GREEN}🚨 エラー監視${NC}"
if [ -f "$LATEST_LOG" ]; then
    ERROR_COUNT=$(grep -i "error\|failed\|exception" "$LATEST_LOG" | wc -l)
    if [ $ERROR_COUNT -gt 0 ]; then
        echo -e "最新実行のエラー: ${RED}$ERROR_COUNT${NC} 件"
        echo -e "${YELLOW}主なエラー:${NC}"
        grep -i "error\|failed" "$LATEST_LOG" | head -3
    else
        echo -e "最新実行のエラー: ${GREEN}0${NC} 件 ✅"
    fi
fi

# PR作成状況
echo -e "\n${GREEN}🔀 PR作成状況${NC}"
if [ -f "$LATEST_LOG" ]; then
    PR_SUCCESS=$(grep -o "PR #[0-9]*" "$LATEST_LOG" | tail -1 || echo "")
    AUTO_MERGE=$(grep "Successfully auto-merged" "$LATEST_LOG" | wc -l)
    
    if [ -n "$PR_SUCCESS" ]; then
        echo -e "最新PR: ${GREEN}$PR_SUCCESS${NC} ✅"
        if [ $AUTO_MERGE -gt 0 ]; then
            echo -e "自動マージ: ${GREEN}成功${NC} ✅"
        fi
    else
        echo -e "最新実行でPR作成なし"
    fi
fi

# 次回実行予定
echo -e "\n${GREEN}⏰ 次回実行予定${NC}"
CURRENT_MIN=$(date +%-M)  # Leading zero を除去
CURRENT_HOUR=$(date +%-H)
NEXT_MIN=$(( (($CURRENT_MIN / 10 + 1) * 10) % 60 ))
if [ $NEXT_MIN -eq 0 ]; then
    NEXT_HOUR=$(( $CURRENT_HOUR + 1 ))
else
    NEXT_HOUR=$CURRENT_HOUR
fi
WAIT_MIN=$(( $NEXT_MIN == 0 ? 60 - $CURRENT_MIN : $NEXT_MIN - $CURRENT_MIN ))
echo -e "次回実行: ${YELLOW}$(printf "%02d:%02d" $NEXT_HOUR $NEXT_MIN)${NC} （約${WAIT_MIN}分後）"

# リアルタイム監視オプション
echo -e "\n${BLUE}💡 ヒント:${NC}"
echo "  - リアルタイム監視: watch -n 30 $0"
echo "  - ログ追跡: tail -f $LOG_DIR/enhanced_auto_pr/*.log"
echo "  - ダッシュボード: ./scripts/start_monitoring_dashboard.sh"

echo -e "\n${BLUE}================================================${NC}"