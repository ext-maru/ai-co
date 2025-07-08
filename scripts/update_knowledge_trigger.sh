#!/bin/bash
# ナレッジベース自動更新トリガースクリプト
# 使用方法: ./update_knowledge_trigger.sh <file_path> <event_type>

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
KNOWLEDGE_BASE="$PROJECT_ROOT/knowledge_base"
LOG_FILE="$PROJECT_ROOT/logs/knowledge_update.log"

# ログ関数
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [KNOWLEDGE_UPDATE] $1" | tee -a "$LOG_FILE"
}

# 引数チェック
if [ $# -lt 2 ]; then
    log "ERROR: 引数が不足しています。使用方法: $0 <file_path> <event_type>"
    exit 1
fi

FILE_PATH="$1"
EVENT_TYPE="$2"

log "INFO: ナレッジ更新トリガー開始 - ファイル: $FILE_PATH, イベント: $EVENT_TYPE"

# ファイルパスから更新対象を判定
update_feature_tree=false
update_component_catalog=false
update_system_architecture=false
update_api_specs=false
update_data_structures=false
update_master_kb=false

# ファイルタイプ判定
if [[ "$FILE_PATH" == */workers/* ]]; then
    log "INFO: ワーカーファイルの変更を検出"
    update_feature_tree=true
    update_component_catalog=true
    update_system_architecture=true
    update_master_kb=true
elif [[ "$FILE_PATH" == */commands/* ]]; then
    log "INFO: AIコマンドファイルの変更を検出"
    update_feature_tree=true
    update_component_catalog=true
    update_master_kb=true
elif [[ "$FILE_PATH" == */libs/* ]]; then
    log "INFO: ライブラリファイルの変更を検出"
    update_feature_tree=true
    update_component_catalog=true
    update_master_kb=true
elif [[ "$FILE_PATH" == */core/* ]]; then
    log "INFO: Core基盤ファイルの変更を検出"
    update_feature_tree=true
    update_component_catalog=true
    update_system_architecture=true
    update_api_specs=true
    update_data_structures=true
    update_master_kb=true
elif [[ "$FILE_PATH" == */config/* ]]; then
    log "INFO: 設定ファイルの変更を検出"
    update_system_architecture=true
    update_api_specs=true
    update_master_kb=true
else
    log "INFO: 対象外ファイルのため更新をスキップ"
    exit 0
fi

# 更新実行関数
update_knowledge_file() {
    local file_name="$1"
    local file_path="$KNOWLEDGE_BASE/$file_name"
    
    log "INFO: $file_name の更新を開始"
    
    # ファイルが存在しない場合はスキップ
    if [ ! -f "$file_path" ]; then
        log "WARN: $file_path が見つかりません。スキップします。"
        return 1
    fi
    
    # 最終更新日を更新
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/最終更新: [0-9-]*/最終更新: $(date '+%Y-%m-%d')/" "$file_path"
    else
        # Linux
        sed -i "s/最終更新: [0-9-]*/最終更新: $(date '+%Y-%m-%d')/" "$file_path"
    fi
    
    log "INFO: $file_name の最終更新日を更新しました"
    return 0
}

# AI送信による更新実行関数
trigger_ai_update() {
    local target="$1"
    local description="$2"
    
    log "INFO: AI経由での$target更新を開始"
    
    # AI Companyが起動中かチェック
    if ! pgrep -f "pm_worker.py" > /dev/null; then
        log "WARN: AI Companyが起動していません。手動更新をスキップします。"
        return 1
    fi
    
    # AIタスクとして送信
    cd "$PROJECT_ROOT"
    if command -v ai-send > /dev/null; then
        ai-send "$description: $FILE_PATH が変更されました。$target を更新してください。" \
            --priority 7 \
            --tags "knowledge,update,auto" 2>/dev/null || {
            log "WARN: ai-send コマンドの実行に失敗しました"
            return 1
        }
        log "INFO: $target の更新タスクをAIに送信しました"
    else
        log "WARN: ai-send コマンドが見つかりません"
        return 1
    fi
}

# 更新処理実行
error_count=0

if [ "$update_feature_tree" = true ]; then
    update_knowledge_file "FEATURE_TREE.md" || ((error_count++))
    trigger_ai_update "機能ツリー" "新機能追加によるFEATURE_TREE.md更新" || ((error_count++))
fi

if [ "$update_component_catalog" = true ]; then
    update_knowledge_file "component_catalog.md" || ((error_count++))
    trigger_ai_update "コンポーネントカタログ" "新コンポーネント追加によるcomponent_catalog.md更新" || ((error_count++))
fi

if [ "$update_system_architecture" = true ]; then
    update_knowledge_file "system_architecture.md" || ((error_count++))
    trigger_ai_update "システムアーキテクチャ" "アーキテクチャ変更によるsystem_architecture.md更新" || ((error_count++))
fi

if [ "$update_api_specs" = true ]; then
    update_knowledge_file "api_specifications.md" || ((error_count++))
    trigger_ai_update "API仕様" "API変更によるapi_specifications.md更新" || ((error_count++))
fi

if [ "$update_data_structures" = true ]; then
    update_knowledge_file "data_structures.md" || ((error_count++))
    trigger_ai_update "データ構造" "データ構造変更によるdata_structures.md更新" || ((error_count++))
fi

if [ "$update_master_kb" = true ]; then
    update_knowledge_file "AI_COMPANY_MASTER_KB_v5.3.md" || ((error_count++))
    trigger_ai_update "マスターナレッジベース" "システム変更によるマスターKB更新" || ((error_count++))
fi

# 統合ナレッジ更新を実行
log "INFO: ナレッジ統合処理を開始"
if command -v ai-knowledge > /dev/null; then
    cd "$PROJECT_ROOT"
    ai-knowledge consolidate --quiet 2>/dev/null || {
        log "WARN: ナレッジ統合処理に失敗しました"
        ((error_count++))
    }
else
    log "WARN: ai-knowledge コマンドが見つかりません"
    ((error_count++))
fi

# 結果レポート
if [ $error_count -eq 0 ]; then
    log "INFO: ナレッジベース更新が正常に完了しました"
    
    # Slack通知（オプション）
    if command -v ai-slack > /dev/null; then
        ai-slack status "📚 ナレッジベース自動更新完了: $FILE_PATH" 2>/dev/null || true
    fi
    
    exit 0
else
    log "ERROR: ナレッジベース更新中に $error_count 個のエラーが発生しました"
    
    # Slack通知（オプション）
    if command -v ai-slack > /dev/null; then
        ai-slack status "⚠️ ナレッジベース更新でエラー発生: $error_count 件" 2>/dev/null || true
    fi
    
    exit 1
fi