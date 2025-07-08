#!/bin/bash
# ナレッジベース監視システムセットアップスクリプト
# 使用方法: ./setup_knowledge_monitoring.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/logs/knowledge_setup.log"

# ログ関数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [SETUP] $1" | tee -a "$LOG_FILE"
}

log "INFO: ナレッジベース監視システムのセットアップを開始します"

# 必要なディレクトリの作成
mkdir -p "$PROJECT_ROOT/logs"
mkdir -p "$PROJECT_ROOT/tmp"

# 1. inotifywaitの確認とインストール
log "INFO: inotifywaitの確認"
if ! command -v inotifywait > /dev/null; then
    log "INFO: inotify-toolsのインストールを試行"
    if command -v apt-get > /dev/null; then
        sudo apt-get update && sudo apt-get install -y inotify-tools
    elif command -v yum > /dev/null; then
        sudo yum install -y inotify-tools
    elif command -v brew > /dev/null; then
        brew install inotify-tools
    else
        log "ERROR: inotify-toolsをインストールできませんでした。手動でインストールしてください。"
        exit 1
    fi
else
    log "INFO: inotifywaitが利用可能です"
fi

# 2. ファイル監視スクリプトの作成
log "INFO: ファイル監視スクリプトを作成"
cat > "$PROJECT_ROOT/scripts/knowledge_file_monitor.sh" << 'EOF'
#!/bin/bash
# ナレッジベースファイル監視デーモン

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/tmp/knowledge_monitor.pid"
LOG_FILE="$PROJECT_ROOT/logs/knowledge_monitor.log"

# ログ関数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [MONITOR] $1" | tee -a "$LOG_FILE"
}

# PIDファイルのチェック
if [ -f "$PID_FILE" ]; then
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        log "ERROR: 監視プロセスが既に実行中です (PID: $(cat "$PID_FILE"))"
        exit 1
    else
        rm -f "$PID_FILE"
    fi
fi

# PIDファイルの作成
echo $$ > "$PID_FILE"

# 監視開始
log "INFO: ナレッジベースファイル監視を開始します"

# シグナルハンドラー
cleanup() {
    log "INFO: 監視プロセスを終了します"
    rm -f "$PID_FILE"
    exit 0
}
trap cleanup SIGINT SIGTERM

# ファイル監視の実行
inotifywait -m -r -e create,modify,delete,move \
    "$PROJECT_ROOT/workers/" \
    "$PROJECT_ROOT/commands/" \
    "$PROJECT_ROOT/libs/" \
    "$PROJECT_ROOT/core/" \
    "$PROJECT_ROOT/config/" \
    --format '%w%f %e' 2>/dev/null | while read file event; do
    
    # 一時ファイルや無関係なファイルをスキップ
    if [[ "$file" == *".swp" ]] || [[ "$file" == *".tmp" ]] || [[ "$file" == *"__pycache__"* ]]; then
        continue
    fi
    
    log "INFO: ファイル変更検出: $file ($event)"
    
    # 変更から少し待ってから処理（連続する変更をまとめる）
    sleep 1
    
    # 更新トリガーを実行
    "$PROJECT_ROOT/scripts/update_knowledge_trigger.sh" "$file" "$event" &
done
EOF

chmod +x "$PROJECT_ROOT/scripts/knowledge_file_monitor.sh"

# 3. Gitフックの設定
log "INFO: Gitフックを設定"
if [ -d "$PROJECT_ROOT/.git" ]; then
    cat > "$PROJECT_ROOT/.git/hooks/post-commit" << 'EOF'
#!/bin/bash
# ナレッジベース Git フック

PROJECT_ROOT="$(git rev-parse --show-toplevel)"
changed_files=$(git diff --name-only HEAD~1 HEAD)

# ナレッジ関連ファイルの変更をチェック
for file in $changed_files; do
    if [[ "$file" == workers/* ]] || [[ "$file" == commands/* ]] || [[ "$file" == libs/* ]] || [[ "$file" == core/* ]] || [[ "$file" == config/* ]]; then
        echo "$(date): Git commit detected knowledge-related change: $file" >> "$PROJECT_ROOT/logs/knowledge_git.log"
        "$PROJECT_ROOT/scripts/update_knowledge_trigger.sh" "$PROJECT_ROOT/$file" "git_commit" &
        break
    fi
done
EOF
    
    chmod +x "$PROJECT_ROOT/.git/hooks/post-commit"
    log "INFO: Git post-commitフックを設定しました"
else
    log "WARN: .gitディレクトリが見つかりません。Gitフックをスキップします。"
fi

# 4. Cronジョブの設定
log "INFO: Cronジョブの設定例を作成"
cat > "$PROJECT_ROOT/scripts/crontab_knowledge.txt" << EOF
# AI Company ナレッジベース自動更新 Cronジョブ
# 適用方法: crontab -e で以下を追加

# 毎日午前3時: ナレッジ統合
0 3 * * * cd $PROJECT_ROOT && ai-knowledge consolidate --quiet >> $PROJECT_ROOT/logs/cron_knowledge.log 2>&1

# 6時間ごと: 進化追跡
0 */6 * * * cd $PROJECT_ROOT && ai-knowledge evolve --quiet >> $PROJECT_ROOT/logs/cron_knowledge.log 2>&1

# 毎週月曜9時: 週次レポート
0 9 * * 1 cd $PROJECT_ROOT && $PROJECT_ROOT/scripts/weekly_knowledge_report.sh >> $PROJECT_ROOT/logs/cron_knowledge.log 2>&1

# 毎月1日: 月次アーカイブ
0 0 1 * * cd $PROJECT_ROOT && $PROJECT_ROOT/scripts/monthly_knowledge_archive.sh >> $PROJECT_ROOT/logs/cron_knowledge.log 2>&1
EOF

# 5. 監視制御スクリプトの作成
log "INFO: 監視制御スクリプトを作成"
cat > "$PROJECT_ROOT/scripts/knowledge_monitor_control.sh" << 'EOF'
#!/bin/bash
# ナレッジベース監視制御スクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PID_FILE="$PROJECT_ROOT/tmp/knowledge_monitor.pid"

case "$1" in
    start)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "ERROR: 監視プロセスが既に実行中です (PID: $(cat "$PID_FILE"))"
            exit 1
        fi
        echo "INFO: ナレッジベース監視を開始します"
        nohup "$PROJECT_ROOT/scripts/knowledge_file_monitor.sh" > /dev/null 2>&1 &
        echo "INFO: 監視プロセスを開始しました (PID: $!)"
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if kill -0 "$PID" 2>/dev/null; then
                kill "$PID"
                rm -f "$PID_FILE"
                echo "INFO: 監視プロセスを停止しました (PID: $PID)"
            else
                echo "WARN: PIDファイルは存在しますが、プロセスが見つかりません"
                rm -f "$PID_FILE"
            fi
        else
            echo "INFO: 監視プロセスは実行されていません"
        fi
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
            echo "INFO: 監視プロセスが実行中です (PID: $(cat "$PID_FILE"))"
        else
            echo "INFO: 監視プロセスは停止しています"
        fi
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "使用方法: $0 {start|stop|status|restart}"
        exit 1
        ;;
esac
EOF

chmod +x "$PROJECT_ROOT/scripts/knowledge_monitor_control.sh"

# 6. 新しいAIコマンドの作成
log "INFO: ai-knowledge-monitor コマンドを作成"
cat > "$PROJECT_ROOT/commands/ai-knowledge-monitor" << 'EOF'
#!/bin/bash
# AI Company ナレッジベース監視管理コマンド

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

exec "$PROJECT_ROOT/scripts/knowledge_monitor_control.sh" "$@"
EOF

chmod +x "$PROJECT_ROOT/commands/ai-knowledge-monitor"

# 7. 検証スクリプトの作成
log "INFO: ナレッジ整合性検証スクリプトを作成"
cat > "$PROJECT_ROOT/scripts/validate_knowledge_integrity.sh" << 'EOF'
#!/bin/bash
# ナレッジベース整合性検証スクリプト

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
KNOWLEDGE_BASE="$PROJECT_ROOT/knowledge_base"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [VALIDATION] $1"
}

log "INFO: ナレッジベース整合性検証を開始"

error_count=0

# 1. 必須ファイルの存在確認
required_files=(
    "FEATURE_TREE.md"
    "component_catalog.md"
    "system_architecture.md"
    "api_specifications.md"
    "data_structures.md"
    "AI_COMPANY_MASTER_KB_v5.3.md"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$KNOWLEDGE_BASE/$file" ]; then
        log "ERROR: 必須ファイルが見つかりません: $file"
        ((error_count++))
    fi
done

# 2. リンク整合性チェック（簡易）
log "INFO: リンク整合性をチェック"
for file in "$KNOWLEDGE_BASE"/*.md; do
    if [ -f "$file" ]; then
        # Markdownリンクの簡易チェック
        broken_links=$(grep -o '\[.*\](\.\/.*\.md)' "$file" | while read link; do
            target=$(echo "$link" | sed 's/.*(\.\///' | sed 's/).*//')
            if [ ! -f "$KNOWLEDGE_BASE/$target" ]; then
                echo "$file: $link"
            fi
        done)
        
        if [ -n "$broken_links" ]; then
            log "WARN: 壊れたリンクを検出: $broken_links"
            ((error_count++))
        fi
    fi
done

# 3. 最終更新日の一貫性チェック
log "INFO: 最終更新日の一貫性をチェック"
today=$(date '+%Y-%m-%d')
for file in "${required_files[@]}"; do
    if [ -f "$KNOWLEDGE_BASE/$file" ]; then
        last_update=$(grep "最終更新:" "$KNOWLEDGE_BASE/$file" | head -1 | sed 's/.*最終更新: //')
        if [ "$last_update" != "$today" ]; then
            log "WARN: $file の最終更新日が古い可能性があります: $last_update"
        fi
    fi
done

# 結果レポート
if [ $error_count -eq 0 ]; then
    log "INFO: ナレッジベース整合性検証が正常に完了しました"
    exit 0
else
    log "ERROR: $error_count 個の問題が検出されました"
    exit 1
fi
EOF

chmod +x "$PROJECT_ROOT/scripts/validate_knowledge_integrity.sh"

# セットアップ完了
log "INFO: ナレッジベース監視システムのセットアップが完了しました"

echo ""
echo "=== セットアップ完了 ==="
echo "作成されたファイル:"
echo "- $PROJECT_ROOT/scripts/knowledge_file_monitor.sh"
echo "- $PROJECT_ROOT/scripts/knowledge_monitor_control.sh"
echo "- $PROJECT_ROOT/scripts/validate_knowledge_integrity.sh"
echo "- $PROJECT_ROOT/commands/ai-knowledge-monitor"
echo "- $PROJECT_ROOT/.git/hooks/post-commit (Gitリポジトリの場合)"
echo ""
echo "使用方法:"
echo "1. 監視開始: ai-knowledge-monitor start"
echo "2. 監視停止: ai-knowledge-monitor stop"
echo "3. 監視状態: ai-knowledge-monitor status"
echo "4. 整合性検証: ./scripts/validate_knowledge_integrity.sh"
echo ""
echo "Cronジョブ設定例: cat $PROJECT_ROOT/scripts/crontab_knowledge.txt"