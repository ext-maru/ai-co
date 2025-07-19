#!/bin/bash
#
# Enhanced Auto PR Processor Cron Script
# PR作成機能付きGitHubイシュー自動処理システム
#

# スクリプトのディレクトリを取得
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ログディレクトリ
LOG_DIR="$PROJECT_ROOT/logs/enhanced_auto_pr"
mkdir -p "$LOG_DIR"

# ログファイル名（日付付き）
LOG_FILE="$LOG_DIR/$(date +%Y%m%d_%H%M%S).log"

# タイムスタンプ付きロギング関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 環境変数の読み込み
if [ -f ~/.bashrc ]; then
    source ~/.bashrc
fi

# 環境変数のチェック
if [ -z "$GITHUB_TOKEN" ]; then
    log "❌ エラー: GITHUB_TOKEN環境変数が設定されていません"
    exit 1
fi

# GitHub関連環境変数の設定
export GITHUB_REPOSITORY="ext-maru/ai-co"
export GITHUB_REPO_OWNER="ext-maru"
export GITHUB_REPO_NAME="ai-co"

log "🚀 Enhanced Auto PR Processor 起動"
log "🔧 環境変数設定:"
log "   GITHUB_TOKEN: ${GITHUB_TOKEN:0:10}..."
log "   GITHUB_REPOSITORY: $GITHUB_REPOSITORY"

# Python環境に移動
cd "$PROJECT_ROOT"

# Enhanced処理実行
log "🔍 Enhanced Auto PR Processor 実行中..."

# 統合された自動Issue処理システムを使用
python3 -c "
import asyncio
import json
import sys
sys.path.append('$PROJECT_ROOT')

from libs.integrations.github.auto_issue_processor import AutoIssueProcessor

async def main():
    processor = AutoIssueProcessor()

    # まずスキャン
    scan_result = await processor.process_request({'mode': 'scan'})
    print(json.dumps(scan_result, indent=2, ensure_ascii=False))

    if scan_result['status'] == 'success' and scan_result['processable_issues'] > 0:
        # 処理実行
        print('\n処理を開始します...')
        process_result = await processor.process_request({'mode': 'process'})
        print(json.dumps(process_result, indent=2, ensure_ascii=False))

        return process_result
    else:
        print('処理可能なイシューがありません')
        return {'status': 'no_issues'}

result = asyncio.run(main())
sys.exit(0 if result.get('status') in ['success', 'no_issues'] else 1)
" 2>&1 | tee -a "$LOG_FILE"

RESULT=${PIPESTATUS[0]}

if [ $RESULT -eq 0 ]; then
    log "✅ Enhanced Auto PR Processor 成功"
else
    log "❌ Enhanced Auto PR Processor 失敗 (exit code: $RESULT)"
fi

# 古いログファイルの削除（7日以上前）
find "$LOG_DIR" -name "*.log" -mtime +7 -delete

log "🏁 Enhanced Auto PR Processor 終了"
exit $RESULT
