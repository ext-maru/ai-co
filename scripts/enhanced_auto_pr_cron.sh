#!/bin/bash

# 🤖 Enhanced Auto PR Cron Script
# エルダーズギルド自動Issue処理システム
# 作成者: クロードエルダー
# 作成日: 2025-07-19

# エラー時即座停止
set -e

# ログ設定
SCRIPT_DIR="/home/aicompany/ai_co"
LOG_DIR="$SCRIPT_DIR/logs/enhanced_auto_pr"
LOG_FILE="$LOG_DIR/cron_$(date +%Y%m%d).log"

# ログディレクトリ作成
mkdir -p "$LOG_DIR"

# ログ関数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [CRON] $1" | tee -a "$LOG_FILE"
}

log "🚀 Enhanced Auto PR Cron 開始"

# 作業ディレクトリ移動
cd "$SCRIPT_DIR" || {
    log "❌ エラー: スクリプトディレクトリに移動できません: $SCRIPT_DIR"
    exit 1
}

# Python仮想環境スキップ（壊れているため）
log "📦 システムPythonを使用（仮想環境は一時的にスキップ）"

# 依存関係確認
log "🔍 依存関係確認中..."
python3 -c "import requests, datetime" 2>/dev/null || {
    log "❌ エラー: 必要なPythonモジュールが不足しています"
    exit 1
}

# Enhanced Auto Issue Processor実行
log "🔄 Enhanced Auto Issue Processor実行開始"

# GitHub Token確認
if [ -z "$GITHUB_TOKEN" ]; then
    log "❌ エラー: GITHUB_TOKEN環境変数が設定されていません"
    exit 1
fi

# プロセッサー実行（正しいモジュールパスで実行）
cd "$SCRIPT_DIR" && python3 -m libs.integrations.github.enhanced_auto_issue_processor 2>&1 | while read line; do
    log "    $line"
done

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    log "✅ Enhanced Auto Issue Processor正常終了"
else
    log "❌ Enhanced Auto Issue Processor異常終了 (exit code: $EXIT_CODE)"

    # エラー通知（オプション）
    if command -v mail >/dev/null 2>&1; then
        echo "Enhanced Auto PR Cron failed at $(date)" | mail -s "Auto Issue Processor Error" root 2>/dev/null || true
    fi
fi

# リソース使用量記録
if command -v ps >/dev/null 2>&1; then
    MEMORY_USAGE=$(ps aux | grep python3 | grep -v grep | awk '{sum+=$4} END {print sum}')
    log "📊 メモリ使用量: ${MEMORY_USAGE}%"
fi

# ディスク使用量確認
DISK_USAGE=$(df "$SCRIPT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
log "💽 ディスク使用量: ${DISK_USAGE}%"

if [ "$DISK_USAGE" -gt 90 ]; then
    log "⚠️  警告: ディスク使用量が90%を超えています"
fi

# ログローテーション（7日以上古いログを削除）
find "$LOG_DIR" -name "cron_*.log" -mtime +7 -delete 2>/dev/null || true

log "🏁 Enhanced Auto PR Cron完了 (exit code: $EXIT_CODE)"

exit $EXIT_CODE
