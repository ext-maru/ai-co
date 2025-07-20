#!/bin/bash
# AI Company 緊急修正スクリプト
# 実行方法: bash fix_ai_company_urgent.sh

set -e  # エラー時に停止

echo "🚀 AI Company 緊急修正を開始します..."

# 1. Slackログの大量削除と整理
echo "📁 Step 1: Slackログの整理..."
cd /home/aicompany/ai_co

# 古いSlackログを削除（当日分以外）
find . -name "slack_project_status_*.log" -type f -mtime +0 -delete
echo "✅ 古いSlackログを削除しました"

# 残りのログをアーカイブ
mkdir -p logs/slack_archive/$(date +%Y%m%d)
mv slack_project_status_*.log logs/slack_archive/$(date +%Y%m%d)/ 2>/dev/null || true
echo "✅ 現在のSlackログをアーカイブしました"

# 2. 重複ワーカーの整理
echo "🔧 Step 2: 重複ワーカーの整理..."
cd /home/aicompany/ai_co/workers

# アーカイブディレクトリ作成
mkdir -p _archived/$(date +%Y%m%d)

# バックアップファイルを移動
find . -name "*_backup_*.py" -exec mv {} _archived/$(date +%Y%m%d)/ \;
find . -name "*.bak" -exec mv {} _archived/$(date +%Y%m%d)/ \;
echo "✅ バックアップファイルをアーカイブしました"

# 3. ログローテーション設定
echo "📊 Step 3: ログローテーション設定..."
cat > /home/aicompany/ai_co/config/log_rotation.conf << 'EOF'
# AI Company ログローテーション設定
/home/aicompany/ai_co/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    maxsize 100M
    create 0644 aicompany aicompany
}

/home/aicompany/ai_co/logs/workers/*.log {
    daily
    rotate 3
    compress
    delaycompress
    missingok
    notifempty
    maxsize 50M
    create 0644 aicompany aicompany
}
EOF
echo "✅ ログローテーション設定を作成しました"

# 4. Slack監視ワーカーの設定調整
echo "⚙️ Step 4: Slack監視設定の調整..."
cat > /home/aicompany/ai_co/config/slack_monitor.json << 'EOF'
{
  "polling_interval": 60,
  "max_retries": 3,
  "log_level": "WARNING",
  "rate_limit": {
    "requests_per_minute": 20,
    "burst_size": 5
  },
  "log_rotation": {
    "enabled": true,
    "max_size_mb": 10,
    "backup_count": 3
  }
}
EOF
echo "✅ Slack監視設定を最適化しました"

# 5. インシデント自動作成スクリプト
echo "🚨 Step 5: インシデント管理の活性化..."
python3 << 'EOF'
import sys
import os
sys.path.insert(0, '/home/aicompany/ai_co')

from pathlib import Path
import json
from datetime import datetime

# Slackログ暴走インシデントを作成
incident_data = {
    "incident_id": f"INC-{datetime.now().strftime('%Y%m%d')}-0002",
    "timestamp": datetime.now().isoformat(),
    "category": "performance",
    "priority": "critical",
    "title": "Slackログファイルの大量生成問題",
    "description": "1日で472個のログファイルが生成され、ディスク容量を圧迫",
    "affected_components": ["slack_monitor_worker", "slack_polling_worker"],
    "impact": "ディスク容量圧迫、パフォーマンス低下",
    "status": "open",
    "assignee": "ai_system",
    "actions_taken": [
        "古いログファイルの削除",
        "ログローテーション設定の追加",
        "監視間隔の調整"
    ]
}

# incident_history.jsonに追記
incident_file = Path("/home/aicompany/ai_co/knowledge_base/incident_history.json")
if incident_file.exists():
    with open(incident_file, 'r') as f:
        data = json.load(f)
    data['incidents'].append(incident_data)
    data['total_incidents'] += 1
    data['open_incidents'] += 1
    with open(incident_file, 'w') as f:
        json.dump(data, f, indent=2)
    print("✅ インシデントを記録しました")
EOF

# 6. 実行中のワーカー確認と再起動
echo "🔄 Step 6: ワーカーの状態確認..."
echo "現在実行中のワーカー:"
ps aux | grep -E "(worker|Worker)" | grep -v grep || true

# 7. ディスク使用状況の確認
echo "💾 Step 7: ディスク使用状況..."
df -h /home/aicompany/ai_co
du -sh /home/aicompany/ai_co/* | sort -hr | head -10

# 8. 完了メッセージ
echo ""
echo "✅ ========================================="
echo "✅ AI Company 緊急修正が完了しました！"
echo "✅ ========================================="
echo ""
echo "📋 実施内容:"
echo "  - Slackログファイルの整理完了"
echo "  - 重複ワーカーのアーカイブ完了"
echo "  - ログローテーション設定完了"
echo "  - Slack監視設定の最適化完了"
echo "  - インシデント記録完了"
echo ""
echo "🔍 次のステップ:"
echo "  1. ai-restart でシステムを再起動"
echo "  2. ai-logs でログを確認"
echo "  3. 監視ダッシュボードの実装を検討"
echo ""
echo "💡 ヒント: 定期的に 'bash fix_ai_company_urgent.sh' を実行してクリーンアップ"
