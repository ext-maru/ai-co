#!/bin/bash
# nWo Library Update Cron Script
# Think it, Rule it, Own it - 開発界新世界秩序の自動ライブラリアップデート
#
# エルダーズギルド評議会承認済み - 2025年7月11日
#
# 使用方法:
# 1. chmod +x scripts/nwo_library_update_cron.sh
# 2. crontab -e で以下を追加:
#    # nWo Library Update - 毎日午前3時
#    0 3 * * * /home/aicompany/ai_co/scripts/nwo_library_update_cron.sh
#
#    # nWo Security Update - 4時間毎
#    0 */4 * * * /home/aicompany/ai_co/scripts/nwo_library_update_cron.sh --security-only
#
#    # nWo Strategic Update - 週1回日曜日
#    0 4 * * 0 /home/aicompany/ai_co/scripts/nwo_library_update_cron.sh --strategic-only

set -e

# 設定
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_CMD="python3"
LOG_DIR="$PROJECT_DIR/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="$LOG_DIR/nwo_library_update_$TIMESTAMP.log"

# ログディレクトリ作成
mkdir -p "$LOG_DIR"

# ログ関数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# エラーハンドリング
error_exit() {
    log "ERROR: $1"

    # エルダー評議会に緊急報告
    if command -v "$PYTHON_CMD" >/dev/null 2>&1; then
        cd "$PROJECT_DIR"
        $PYTHON_CMD -c "
import sys
sys.path.append('.')
from libs.elder_council import ElderCouncil
import asyncio

async def emergency_report():
    council = ElderCouncil()
    await council.emergency_report(
        'nWo Library Update Cron Failure',
        'cron実行エラー: $1',
        'high'
    )

asyncio.run(emergency_report())
" 2>/dev/null || log "ERROR: エルダー評議会への報告失敗"
    fi

    exit 1
}

# 引数解析
COMMAND_ARGS=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --security-only)
            COMMAND_ARGS="--security-only"
            log "🚨 nWo Security Update Mode"
            shift
            ;;
        --strategic-only)
            COMMAND_ARGS="--strategic-only"
            log "🎯 nWo Strategic Update Mode"
            shift
            ;;
        --analyze-only)
            COMMAND_ARGS="--analyze-only"
            log "🔍 nWo Analyze Only Mode"
            shift
            ;;
        --dry-run)
            COMMAND_ARGS="--dry-run"
            log "📋 nWo Dry Run Mode"
            shift
            ;;
        --force-update)
            COMMAND_ARGS="--force-update"
            log "⚡ nWo Force Update Mode"
            shift
            ;;
        *)
            log "Unknown option: $1"
            shift
            ;;
    esac
done

# デフォルトはフルサイクル
if [[ -z "$COMMAND_ARGS" ]]; then
    log "🌟 nWo Full Cycle Mode"
fi

# 前処理
log "🌟 nWo Library Update Cron Started"
log "📂 Project Directory: $PROJECT_DIR"
log "📄 Log File: $LOG_FILE"

# プロジェクトディレクトリに移動
cd "$PROJECT_DIR" || error_exit "プロジェクトディレクトリへの移動失敗"

# Python環境確認
if ! command -v "$PYTHON_CMD" >/dev/null 2>&1; then
    error_exit "Python3が見つかりません"
fi

# 仮想環境の確認・アクティベート
if [[ -f "venv/bin/activate" ]]; then
    log "📦 仮想環境をアクティベート"
    source venv/bin/activate
elif [[ -f ".venv/bin/activate" ]]; then
    log "📦 仮想環境をアクティベート"
    source .venv/bin/activate
else
    log "⚠️ 仮想環境が見つかりません。システムPythonを使用"
fi

# 依存関係確認
log "🔍 依存関係確認中..."
if ! $PYTHON_CMD -c "import requests, packaging, semver" 2>/dev/null; then
    log "📦 必要な依存関係をインストール中..."
    pip install requests packaging semver || error_exit "依存関係インストール失敗"
fi

# システムヘルスチェック
log "🏥 システムヘルスチェック実行中..."
if ! $PYTHON_CMD -c "
import sys
sys.path.append('.')
try:
    from libs.nwo_library_update_strategy import nWoLibraryUpdateStrategy
    print('✅ nWoライブラリアップデート戦略システム正常')
except ImportError as e:
    print(f'❌ インポートエラー: {e}')
    sys.exit(1)
" 2>&1 | tee -a "$LOG_FILE"; then
    error_exit "システムヘルスチェック失敗"
fi

# メインコマンド実行
log "🚀 nWo Library Update Command 実行中..."
if ! $PYTHON_CMD "commands/ai_nwo_library_update.py" $COMMAND_ARGS 2>&1 | tee -a "$LOG_FILE"; then
    error_exit "nWo Library Update Command 実行失敗"
fi

# 実行結果の確認
if [[ $? -eq 0 ]]; then
    log "✅ nWo Library Update 成功"

    # 成功時のエルダー評議会報告
    $PYTHON_CMD -c "
import sys
sys.path.append('.')
from libs.elder_council import ElderCouncil
import asyncio

async def success_report():
    council = ElderCouncil()
    await council.log_activity(
        'nWo Library Update Success',
        'cron実行成功: $COMMAND_ARGS',
        'info'
    )

asyncio.run(success_report())
" 2>/dev/null || log "WARNING: エルダー評議会への成功報告失敗"

else
    error_exit "nWo Library Update 実行失敗"
fi

# ログローテーション（30日以上古いログを削除）
log "🗑️ ログローテーション実行中..."
find "$LOG_DIR" -name "nwo_library_update_*.log" -type f -mtime +30 -delete 2>/dev/null || true

# ディスク使用量チェック
DISK_USAGE=$(df "$PROJECT_DIR" | awk 'NR==2 {print $5}' | sed 's/%//')
if [[ $DISK_USAGE -gt 90 ]]; then
    log "⚠️ ディスク使用量が90%を超えています: ${DISK_USAGE}%"

    # エルダー評議会に警告報告
    $PYTHON_CMD -c "
import sys
sys.path.append('.')
from libs.elder_council import ElderCouncil
import asyncio

async def disk_warning():
    council = ElderCouncil()
    await council.log_activity(
        'Disk Usage Warning',
        'ディスク使用量: ${DISK_USAGE}%',
        'warning'
    )

asyncio.run(disk_warning())
" 2>/dev/null || log "WARNING: ディスク使用量警告の報告失敗"
fi

# 統計情報収集
log "📊 統計情報収集中..."
LOG_SIZE=$(wc -l < "$LOG_FILE")
EXECUTION_TIME=$(($(date +%s) - $(date -d "$(head -1 "$LOG_FILE" | cut -d']' -f1 | cut -d'[' -f2)" +%s)))

log "📈 実行統計:"
log "   - ログ行数: $LOG_SIZE"
log "   - 実行時間: ${EXECUTION_TIME}秒"
log "   - ログファイル: $LOG_FILE"

# nWo日次評議会への報告
if [[ -z "$COMMAND_ARGS" ]]; then
    log "🏛️ nWo日次評議会への報告..."
    $PYTHON_CMD "libs/nwo_daily_council.py" --library-update-report "$LOG_FILE" 2>&1 | tee -a "$LOG_FILE" || log "WARNING: nWo日次評議会報告失敗"
fi

# 完了
log "🎉 nWo Library Update Cron 完了"
log "📄 詳細ログ: $LOG_FILE"

# 最終ステータス
exit 0
