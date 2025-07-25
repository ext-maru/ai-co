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
