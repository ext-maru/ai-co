#!/bin/bash
# AI Company 統合管理スクリプト
# 実行方法: bash ai_company_manager.sh [command]

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="/home/aicompany/ai_co"
KNOWLEDGE_DIR="/home/aicompany/ai_co/knowledge_base"

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ヘルプメッセージ
show_help() {
    echo "🏢 AI Company 統合管理スクリプト"
    echo ""
    echo "使用方法: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  health     - システムの健全性をチェック"
    echo "  fix        - 緊急修正を実行"
    echo "  clean      - ログとバックアップをクリーンアップ"
    echo "  report     - 詳細なシステムレポートを生成"
    echo "  restart    - システムを安全に再起動"
    echo "  monitor    - リアルタイム監視を開始"
    echo "  backup     - システムのバックアップを作成"
    echo "  restore    - バックアップから復元"
    echo "  help       - このヘルプを表示"
    echo ""
}

# 健全性チェック
health_check() {
    echo -e "${BLUE}🏥 システム健全性チェックを開始...${NC}"
    python3 ${SCRIPT_DIR}/ai_company_health_check.py
}

# 緊急修正
emergency_fix() {
    echo -e "${RED}🚨 緊急修正を開始...${NC}"

    # 確認プロンプト
    read -p "緊急修正を実行しますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        bash ${SCRIPT_DIR}/fix_ai_company_urgent.sh
    else
        echo "キャンセルしました"
    fi
}

# クリーンアップ
cleanup() {
    echo -e "${YELLOW}🧹 クリーンアップを開始...${NC}"

    cd $PROJECT_ROOT

    # 古いログファイルの削除
    echo "古いログファイルを削除中..."
    find . -name "*.log" -mtime +7 -delete
    find . -name "slack_project_status_*.log" -mtime +1 -delete

    # バックアップファイルの整理
    echo "バックアップファイルを整理中..."
    find . -name "*_backup_*" -o -name "*.bak" | while read file; do
        archive_dir=$(dirname "$file")/_archived/$(date +%Y%m%d)
        mkdir -p "$archive_dir"
        mv "$file" "$archive_dir/"
    done

    # 空のディレクトリを削除
    find . -type d -empty -delete

    echo -e "${GREEN}✅ クリーンアップ完了${NC}"
}

# システムレポート生成
generate_report() {
    echo -e "${BLUE}📊 システムレポートを生成中...${NC}"

    REPORT_FILE="${PROJECT_ROOT}/reports/system_report_$(date +%Y%m%d_%H%M%S).md"
    mkdir -p $(dirname "$REPORT_FILE")

    cat > "$REPORT_FILE" << EOF
# AI Company システムレポート
生成日時: $(date '+%Y年%m月%d日 %H:%M:%S')

## システム概要

### 基本情報
- ホスト名: $(hostname)
- OS: $(lsb_release -d | cut -f2)
- Python: $(python3 --version)
- プロジェクトルート: $PROJECT_ROOT

### ディスク使用状況
\`\`\`
$(df -h $PROJECT_ROOT)
\`\`\`

### 大容量ディレクトリ TOP10
\`\`\`
$(du -sh $PROJECT_ROOT/* | sort -hr | head -10)
\`\`\`

## ワーカー状態

### 実行中のワーカー
\`\`\`
$(ps aux | grep -E "(worker|Worker)" | grep -v grep || echo "実行中のワーカーなし")
\`\`\`

### ワーカーファイル一覧
\`\`\`
$(ls -la $PROJECT_ROOT/workers/*.py | grep -v __pycache__ | head -20)
\`\`\`

## ログ分析

### 最新のエラーログ（直近10件）
\`\`\`
$(grep -i error $PROJECT_ROOT/logs/*.log 2>/dev/null | tail -10 || echo "エラーなし")
\`\`\`

### ログファイルサイズ
\`\`\`
$(find $PROJECT_ROOT -name "*.log" -exec ls -lh {} \; | sort -k5 -hr | head -10)
\`\`\`

## インシデント状況
\`\`\`
$(python3 -c "
import json
with open('$KNOWLEDGE_DIR/incident_history.json', 'r') as f:
    data = json.load(f)
    print(f\"総インシデント: {data['metadata']['total_incidents']}件\")
    print(f\"オープン: {data['metadata']['open_incidents']}件\")
    print(f\"解決済み: {data['metadata']['resolved_incidents']}件\")
" 2>/dev/null || echo "インシデント情報を取得できません")
\`\`\`

## RabbitMQ状態
\`\`\`
$(sudo rabbitmqctl status 2>/dev/null | head -20 || echo "RabbitMQ情報を取得できません")
\`\`\`

## 推奨アクション
$(python3 -c "
import os
import glob

issues = []

# Slackログチェック
slack_logs = len(glob.glob('$PROJECT_ROOT/slack_project_status_*.log'))
if slack_logs > 10:
    issues.append(f'- Slackログファイルが{slack_logs}個存在。クリーンアップを推奨')

# バックアップファイルチェック
backup_files = len(glob.glob('$PROJECT_ROOT/**/*_backup_*', recursive=True))
if backup_files > 0:
    issues.append(f'- バックアップファイルが{backup_files}個存在。整理を推奨')

if issues:
    print('\\n'.join(issues))
else:
    print('- 特に問題は検出されませんでした')
")

---
レポート生成完了: $(date)
EOF

    echo -e "${GREEN}✅ レポートを生成しました: $REPORT_FILE${NC}"
}

# システム再起動
safe_restart() {
    echo -e "${YELLOW}🔄 システムを安全に再起動します...${NC}"

    # 現在の状態を保存
    echo "現在の状態を保存中..."
    generate_report

    # ワーカーを停止
    echo "ワーカーを停止中..."
    ${PROJECT_ROOT}/commands/ai-stop

    sleep 5

    # ワーカーを起動
    echo "ワーカーを起動中..."
    ${PROJECT_ROOT}/commands/ai-start

    echo -e "${GREEN}✅ 再起動完了${NC}"
}

# リアルタイム監視
monitor_system() {
    echo -e "${BLUE}👁️  リアルタイム監視を開始...${NC}"
    echo "Ctrl+C で終了"
    echo ""

    while true; do
        clear
        echo -e "${BLUE}=== AI Company リアルタイム監視 ===${NC}"
        echo "更新時刻: $(date '+%Y-%m-%d %H:%M:%S')"
        echo ""

        # CPU/メモリ使用率
        echo -e "${YELLOW}[システムリソース]${NC}"
        top -bn1 | grep "Cpu\|Mem" | head -2
        echo ""

        # ワーカー状態
        echo -e "${YELLOW}[アクティブワーカー]${NC}"
        ps aux | grep -E "(worker|Worker)" | grep -v grep | wc -l | xargs echo "実行中:"
        echo ""

        # 最新ログ
        echo -e "${YELLOW}[最新ログ (直近5件)]${NC}"
        find $PROJECT_ROOT/logs -name "*.log" -mmin -5 -exec tail -1 {} \; | tail -5
        echo ""

        # ディスク使用率
        echo -e "${YELLOW}[ディスク使用率]${NC}"
        df -h $PROJECT_ROOT | tail -1

        sleep 10
    done
}

# バックアップ作成
create_backup() {
    echo -e "${BLUE}💾 バックアップを作成中...${NC}"

    BACKUP_DIR="${PROJECT_ROOT}/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # 重要なファイルをバックアップ
    echo "設定ファイルをバックアップ中..."
    cp -r $PROJECT_ROOT/config $BACKUP_DIR/
    cp $PROJECT_ROOT/.env $BACKUP_DIR/ 2>/dev/null || true

    echo "ナレッジベースをバックアップ中..."
    cp -r $PROJECT_ROOT/knowledge_base $BACKUP_DIR/

    echo "ワーカーをバックアップ中..."
    cp -r $PROJECT_ROOT/workers $BACKUP_DIR/

    # バックアップ情報を記録
    cat > "$BACKUP_DIR/backup_info.txt" << EOF
バックアップ作成日時: $(date)
システムバージョン: $(git describe --tags --always 2>/dev/null || echo "unknown")
実行ユーザー: $(whoami)
含まれるファイル:
- 設定ファイル (config/)
- 環境変数 (.env)
- ナレッジベース (knowledge_base/)
- ワーカー (workers/)
EOF

    # 圧縮
    echo "圧縮中..."
    cd $(dirname "$BACKUP_DIR")
    tar -czf "$(basename "$BACKUP_DIR").tar.gz" "$(basename "$BACKUP_DIR")"
    rm -rf "$BACKUP_DIR"

    echo -e "${GREEN}✅ バックアップ完了: $(dirname "$BACKUP_DIR")/$(basename "$BACKUP_DIR").tar.gz${NC}"
}

# メイン処理
case "$1" in
    health)
        health_check
        ;;
    fix)
        emergency_fix
        ;;
    clean)
        cleanup
        ;;
    report)
        generate_report
        ;;
    restart)
        safe_restart
        ;;
    monitor)
        monitor_system
        ;;
    backup)
        create_backup
        ;;
    help|"")
        show_help
        ;;
    *)
        echo -e "${RED}不明なコマンド: $1${NC}"
        show_help
        exit 1
        ;;
esac
