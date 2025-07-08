#!/bin/bash
#
# AI Company ログ改善 段階的移行スクリプト
# 既存ワーカーを一つずつプロフェッショナルなログに移行
#

set -e

PROJECT_DIR="/home/aicompany/ai_co"
MIGRATION_LOG="$PROJECT_DIR/logs/log_migration.log"

echo "AI Company Log Migration Tool"
echo "============================="
echo ""

# ログファイル初期化
echo "[$(date)] Log migration started" > "$MIGRATION_LOG"

# 移行対象のワーカー
WORKERS=(
    "task_worker"
    "pm_worker"
    "result_worker"
    "dialog_task_worker"
)

echo "Migration targets:"
for worker in "${WORKERS[@]}"; do
    echo "  - $worker"
done
echo ""

# 関数: ワーカーの絵文字使用状況をチェック
check_worker_emoji_usage() {
    local worker_name=$1
    local log_file="$PROJECT_DIR/logs/${worker_name}.log"
    
    if [ -f "$log_file" ]; then
        local emoji_count=$(grep -o '[🚀✨🎉🌟💡🔥💪😎🎯🎊]' "$log_file" 2>/dev/null | wc -l || echo 0)
        local line_count=$(wc -l < "$log_file")
        local emoji_density=$(awk "BEGIN {printf \"%.1f\", $emoji_count * 100 / $line_count}")
        
        echo "  Emoji usage: $emoji_count emojis in $line_count lines (${emoji_density}% density)"
        echo "[$(date)] $worker_name: $emoji_count emojis, ${emoji_density}% density" >> "$MIGRATION_LOG"
        
        return $emoji_count
    else
        echo "  No log file found"
        return 0
    fi
}

# 関数: ワーカーファイルのバックアップ
backup_worker() {
    local worker_name=$1
    local worker_file="$PROJECT_DIR/workers/${worker_name}.py"
    local backup_file="$PROJECT_DIR/workers/${worker_name}.py.pre_log_improvement"
    
    if [ -f "$worker_file" ] && [ ! -f "$backup_file" ]; then
        cp "$worker_file" "$backup_file"
        echo "  Backup created: $backup_file"
    fi
}

# 関数: 改善推奨事項の生成
generate_improvement_recommendations() {
    local worker_name=$1
    local recommendations_file="$PROJECT_DIR/docs/log_improvement_${worker_name}.md"
    
    cat > "$recommendations_file" << EOF
# Log Improvement Recommendations for ${worker_name}

## Current Issues
1. Excessive emoji usage in logs
2. Subjective expressions instead of objective data
3. Missing performance metrics
4. Lack of structured error information

## Migration Steps

### 1. Update imports
\`\`\`python
from core.improved_base_worker import ImprovedBaseWorker
from core.improved_logging_mixin import ImprovedLoggingMixin
\`\`\`

### 2. Replace log statements

#### Task Start
Before:
\`\`\`python
self.logger.info(f"🚀 Starting amazing task {task_id}!")
\`\`\`

After:
\`\`\`python
self.log_task_start(task_id, task_type)
self.log_metric(task_id, 'queue_time_ms', queue_time)
\`\`\`

#### Task Complete
Before:
\`\`\`python
self.logger.info(f"🎉 Task {task_id} completed perfectly!")
\`\`\`

After:
\`\`\`python
self.log_task_complete(task_id, f"Processed in {duration:.2f}s, {files} files")
\`\`\`

#### Error Handling
Before:
\`\`\`python
self.logger.error(f"😱 Error occurred: {e}")
\`\`\`

After:
\`\`\`python
self.log_task_error(task_id, e, context="processing", will_retry=True)
\`\`\`

### 3. Add metrics tracking
- Processing time
- Number of items processed
- Error rates
- Resource usage

### 4. Update Slack notifications
Use ImprovedSlackNotifier for professional notifications.

## Testing
1. Run with --test flag
2. Check log output for professional format
3. Verify metrics are being tracked
4. Confirm Slack notifications are data-focused
EOF

    echo "  Recommendations created: $recommendations_file"
}

# メイン処理
echo "Starting analysis and migration preparation..."
echo ""

for worker in "${WORKERS[@]}"; do
    echo "Processing: $worker"
    echo "------------------------"
    
    # 現状分析
    echo "Current status:"
    check_worker_emoji_usage "$worker"
    emoji_count=$?
    
    # 改善が必要な場合
    if [ $emoji_count -gt 0 ]; then
        echo "  Status: Improvement needed"
        
        # バックアップ作成
        backup_worker "$worker"
        
        # 推奨事項生成
        generate_improvement_recommendations "$worker"
        
        echo "  Ready for migration"
    else
        echo "  Status: Already professional"
    fi
    
    echo ""
done

# サマリー表示
echo "Migration Summary"
echo "================="
echo ""
echo "1. Review improvement recommendations in docs/log_improvement_*.md"
echo "2. Test improved workers with --test flag"
echo "3. Deploy improved workers one by one"
echo "4. Monitor logs for professional output"
echo ""
echo "Example migration command:"
echo "  cp workers/improved_pm_worker.py workers/pm_worker.py"
echo "  ai-worker-restart pm"
echo ""
echo "Log migration preparation complete!"
echo "Check $MIGRATION_LOG for details"

# 移行状況チェックツール作成
cat > "$PROJECT_DIR/scripts/check_log_migration_status.py" << 'EOF'
#!/usr/bin/env python3
"""
ログ改善移行状況チェックツール
"""

import os
import re
from pathlib import Path
from datetime import datetime

def check_migration_status():
    """移行状況をチェック"""
    project_dir = Path("/home/aicompany/ai_co")
    workers_dir = project_dir / "workers"
    logs_dir = project_dir / "logs"
    
    print("AI Company Log Migration Status")
    print("===============================")
    print(f"Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # ワーカー別チェック
    workers = ["task_worker", "pm_worker", "result_worker", "dialog_task_worker"]
    
    status_summary = {
        "migrated": [],
        "in_progress": [],
        "not_started": []
    }
    
    for worker in workers:
        worker_file = workers_dir / f"{worker}.py"
        log_file = logs_dir / f"{worker}.log"
        
        print(f"\n{worker}:")
        print("-" * 40)
        
        # コードチェック
        if worker_file.exists():
            with open(worker_file, 'r') as f:
                content = f.read()
            
            uses_improved = "ImprovedLoggingMixin" in content or "ImprovedBaseWorker" in content
            has_old_emojis = bool(re.search(r'[🚀✨🎉🌟💡🔥💪😎🎯🎊]', content))
            
            if uses_improved and not has_old_emojis:
                print("  Code status: ✓ Migrated")
                status_summary["migrated"].append(worker)
            elif uses_improved:
                print("  Code status: ⚡ Partially migrated")
                status_summary["in_progress"].append(worker)
            else:
                print("  Code status: ✗ Not migrated")
                status_summary["not_started"].append(worker)
        else:
            print("  Code status: ? File not found")
        
        # ログチェック（最新100行）
        if log_file.exists():
            with open(log_file, 'r') as f:
                lines = f.readlines()[-100:]  # 最新100行
            
            content = ''.join(lines)
            emoji_count = len(re.findall(r'[🚀✨🎉🌟💡🔥💪😎🎯🎊]', content))
            professional_patterns = sum([
                len(re.findall(r'Task started:', content)),
                len(re.findall(r'Task completed:', content)),
                len(re.findall(r'duration: \d+\.\d+s', content)),
                len(re.findall(r'Metric:', content))
            ])
            
            print(f"  Recent logs: {emoji_count} emojis, {professional_patterns} professional patterns")
    
    # サマリー
    print("\n\nMigration Summary:")
    print("==================")
    print(f"✓ Fully migrated: {len(status_summary['migrated'])}")
    print(f"⚡ In progress: {len(status_summary['in_progress'])}")
    print(f"✗ Not started: {len(status_summary['not_started'])}")
    
    # 推奨事項
    if status_summary["not_started"]:
        print("\nNext steps:")
        print(f"1. Start with: {status_summary['not_started'][0]}")
        print("2. Use improved examples as reference")
        print("3. Test thoroughly before deployment")

if __name__ == "__main__":
    check_migration_status()
EOF

chmod +x "$PROJECT_DIR/scripts/check_log_migration_status.py"

echo ""
echo "Status check tool created: scripts/check_log_migration_status.py"
echo "Run it anytime to check migration progress"
